---
artifact: PARIPRASHNA_STREAM_CHARTER_S1
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S1
stream_name: Navigation, Shell & History
frozen_by: Session A, Phase A5
---

# Stream charter — S1 (Navigation, Shell & History)

- **Owner (actor to register):** `lead-s1`
- **Independent verifier (actor to register/use):** `verifier` (default Sonnet/high per elevation §11.1; escalate to a dedicated Opus verifier for any S1-severity/security-class finding, e.g. the cross-chart denial re-proof)
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0` (origin/main, as of CG-2 close)
- **Deployed revision pin — READ THIS FIRST:** `amjis-web` is currently deployed at `cafa894ee7cfc2e86743bb92625e7faf293aec0a`, which is **behind** the baseline SHA above (missing the B-007/B-008 cockpit-authorization fixes — irrelevant to S1's own territory, but the staleness itself is the live fact). The deploy pipeline is failing on an **unrelated** Nirmana-campaign preflight step (PR #1601, "Nirmana evidence ownership handoff"), not on anything Paripraśna-owned. **Re-check `gcloud run services describe amjis-web --format="value(spec.template.spec.containers[0].image)"` at your own session open** — if it still lags baseline, note it and proceed (S1's own territory is unaffected by the cockpit fixes); if it has advanced past a commit you rely on, re-derive.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s1-nav-shell-history`
- **Approved ceiling:** 8h wall-clock; spend — use judgment, favor correctness and independent verification over speed (same standing directive as Session A)
- **Entry gate and dependencies:** CG-2 CLOSED (`gate_closed` event `031e03fc-7685-4c17-af34-bba115318246`); P2→P3 dependency RESOLVED (`dependency_resolved` event `02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status (RESOLVED — A2)

A pre-existing Firebase test principal (`uid hunQRYVJ5Ec2mQnJnutK7AoQnsO2`, `profiles.role='guest'`) already holds exactly one `chart_grants` row: `(chart_id=1c826d5a-41cb-4450-b4dc-59d440e5f75a, permission='view')`, and no grant on any other chart. Mint a session cookie via the repo's existing `platform/scripts/dev/mint_session_cookie.ts` (recipe: `SERVICE_URL=https://amjis-web-qm256lasva-el.a.run.app SUPER_ADMIN_UID=hunQRYVJ5Ec2mQnJnutK7AoQnsO2 COOKIE_OUTPUT_FILE=<path> npx dotenvx run -f platform/.env.local -- npx tsx platform/scripts/dev/mint_session_cookie.ts` from the `platform/` directory) — full detail and a worked cross-chart-denial proof in `../A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`. Delete the minted cookie file after use; never log it; never read the native's real chart's response body beyond status/redirect headers.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan Mohanty) ONLY. The native's real chart `482012f1-710e-4a25-994a-93821f5871aa` is OUT OF BOUNDS beyond a denial-probe target (status/redirect only, never response body).

## Scope (test plan v2.1 §5.1 sidebar/history rows + §8.1–8.2 for shell regions; journeys J1, J7)

**Primary file territory:** `platform/src/components/pariprashna/` shell + sidebar components; history routes (`platform/src/app/api/conversations/*`, history-listing UI).

**Region battery (test plan §5.1, "History sidebar" row):** past readings grouped by chart then recency; active/streaming states unmistakable; collapse state remembered; title, relative time, keyboard activation, empty/loading/error state, long-title truncation. Agent-in-browser proof scenarios named in the plan: (1) revisit a saved reading after refresh and from a second session; (2) locate an old reading unaided; (3) attempt — and be denied — another chart's thread (this is your LIVE-rung cross-chart denial re-proof; reuse the A2 credential and probe pattern).

**Mandatory journeys (test plan §5.2), your assignment per elevation §4/§8.2:** J1 (first visit: orient to the chart, understand the empty state, choose a prompt, ask a question) and J7 (history: return after reload, select a prior thread, rename if permitted, verify no other chart is accessible).

**Additional named scenarios (elevation §11.2 S1 block):** large-history-list performance (component/route/keyboard/visual-regression coverage per §5.1's "Automated coverage" column) and device-return (§5.1 "History, return, memory" row: a settled reading survives refresh, relogin, reconnect, device return, chart switch — private, fast, semantically identical to the sealed original).

**Cross-cutting (shared with S2 by territory, not topic — test plan §8):** §8.1 visual/interaction regression and §8.2 WCAG 2.2 AA accessibility for the shell/sidebar regions specifically (viewport/working/dock/composer regions are S2's territory — resolve any ambiguous a11y/visual overlap by which component territory it lives in, not by which topic it resembles, per elevation §8.3).

**Freeze your own scenario denominator** (per the register law and the charter template) by enumerating the concrete cases above before executing — do not start counting mid-run.

## Evidence rungs required

Per finding: STATIC → REPLAY → INTEGRATION → LIVE → (NATIVE ACCEPTANCE reserved to native, post-G6). The cross-chart denial proof and the "another chart's thread" denial specifically require the LIVE rung (a real request against the deployed service), same evidentiary bar B-001/B-007/B-008 met in A4.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — 11 V3 entries open as of A5 freeze. None are S1-territory-specific yet. Cross-territory findings (e.g. an a11y issue that's actually in S2's viewport territory) go through the referral protocol (elevation §8.3) — file to the owning stream, never fix cross-territory.

**Superseded 2026-08-29 (A5 split):** the shared register's §4 stopped being a live append point — six streams appending there concurrently was producing repeated merge conflicts (see the index's own §4a for the full history). File all NEW S1 findings in `../EDIR_V3_REGISTER_S1_v1_0.md` as `S1-V3-E-0NN` (next id: check that file's frontmatter `id_convention`), never in the shared index or another stream's file. S1's own pre-split entries (S1-V3-E-012/013/014) stay in `../EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md`.

## Posture

Browser-heavy; moderate code tracing. Sonnet/medium for finder/investigator roles, Sonnet/high default for independent verification, escalate to Opus/high for the cross-chart denial LIVE-rung verification specifically (S1-severity/security-class per elevation §11.1's model table).

Record evidence URIs for every accepted work item. Park scope/product-tradeoff decisions to a spawned Native Surrogate (Opus/high), tagged `SURROGATE DECISION — not native acceptance`, tracker-evented. Closure needs stream regression, a result packet (template: `../templates/STREAM_RESULT_PACKET_TEMPLATE.md`), independent verification, and integrator acceptance (CG-3 contribution).
