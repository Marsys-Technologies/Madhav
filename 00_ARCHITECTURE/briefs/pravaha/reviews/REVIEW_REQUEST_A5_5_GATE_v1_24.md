---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.24"
status: "FINAL for dispatch (round 19, narrow) — a SHORT DELTA on v1.23: the re-pin tool at 4df9db116 closes Fable F-R18-1..5 and Codex R18-1..3 (window-clipped edges, validated identity-bound capture); runbook v1.17 and sitting checklist v1.1 close R18-3/R18-4; composed suite 1099 passed in one clean run. Stream A unchanged."
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-03"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.23 (never edited). Everything in v1.23 stands except the tool head, the composed/exhibit heads and the trial-capture comparand, which this page REPLACES."
---

# A5.5 gate — round-19 request: delta for the re-pin tool `4df9db116`

## Heads and results (REPLACE v1.23's)
Stream A **`7678f7722` FROZEN, unchanged** (1240 `05a8f897…bc6b`; lock `893c475a…`; window hashes and trigger manifest unchanged, rehearsal not re-run) · **#2903 re-pin tool `4df9db1160b2e1aa757aceefb6fe5434c384b744`** (file sha256 `3d2ed50e30fe0487957ffd14d79017aeaef3c55f91059ab94030ec7beb41edea`; was `e8f417298`; pushed to the draft PR's branch) · integration ref **`d680a1f20`** · exhibit #2952 **`f28716b5c` (tree-identical to the integration ref)** · docs `campaign/pravaha` `cab6dd3e9`.
- **ONE full composed run on these bytes: 1099 passed in 12m20s, 0 failed, 0 skipped** (1080 + 19 new tool tests). The tool's own file: **100 passed with a disposable PostgreSQL, 98 passed + 2 skipped without one.**

## What changed, by finding
| finding | status | evidence |
|---|---|---|
| **F-R18-1 (P1) window-clipped edges** | **DONE** | Premise first verified on a trial capture and the live columns (reported earlier). The truncation flags are read in the SAME capture transaction and merged into the rows (capture format and checksum changed — an official capture must use this tool). Edges clipped on BOTH builds are excluded from the shift statistics and must be unchanged (bound instants as a cross-check, because level-3 clipped edges are unflagged); a clip on ONE build only STOPs ("window-edge status changed"); clipped counts per level are in the evidence; a level with zero unclipped measurements STOPs. Tests run through `main()` with first and last rows clipped (writer-shaped world); one test does not monkeypatch `remeasure_reference_rows` and uses the ten real reference rows. |
| **F-R18-2 / R18-2** capture validates at acquisition | **DONE** | `--capture-old` runs the loader's own `validate_capture` BEFORE writing: tree problems, contract, reference ids present with lords, flags consistent, the ten natal rows. Malformed ⇒ named STOP, no artifact, rollback + close preserved. Test through the normal capture dispatch. |
| **R18-1** every row validated; identity bound | **DONE** | Every captured row is checked against the old build and the read contract (system vimshottari, ayanāṃśa lahiri_chitrapaksha, tier two_pass_verified, levels 1–3) at capture AND at load. Chart id, build id and the selection contract are bound INTO the data checksum; the whole-file checksum is recorded separately. Regression: an envelope claiming the old pin whose rows carry another build ⇒ exit 3, no application. Capture also retains the tool commit, per-level counts, separate dasha and natal build ids, and the asset-state / build census from the same snapshot. |
| **F-R18-3 / R18-3** checklist | **DONE** (checklist v1.1) | Preamble now says: no routine deploy other than the ones our merges trigger; states what the automatic post-merge run does — read from `deploy.yml` and `migrate.ts` on the integration branch: it carries no window input, so the routine runner REFUSES the first pending protected file by name, the routine-migration step fails and the deploy jobs that need it are skipped (expected RED, nothing applied or deployed, any other message = STOP; to be observed at row 4); cites "Codex round 17 ACCEPT of step (a)"; W4 moved to row 5 with the CONNECT readback and a STOP; post-window W2 recheck in row 9; W5 BOTH directions beside W6's; ONE controlling schedule; the four W3 relations named in row 3; what the manifest is confirmed against stated in row 2. |
| **F-R18-4** notice and W0 | **DONE** | The notice binds system and ayanāṃśa; level-4 (any other level) entries are IGNORED and echoed, not refused; `{start,end}` = the two boundary shifts, not a range; the notice must give the actual LAHIRI L1–3 shifts, not the across-ayanāṃśa range (runbook §5.4). The W0 fallback has a defined format and `--import-w0 --w0-checksum --w0-capture-out` (verified against the named checksum, validated like a capture, re-written with `source = "w0"`). |
| **F-R18-5** apply | **DONE** | Literal-conflict assert at apply (an old literal mapping to two new ones STOPs before writing), UUIDs in canonical form, chart-id guard (`--apply` refused for a non-canonical chart), golden fixtures named beside the lock in the runbook and in the tool's NEXT message; the five stale "accepts the pinned OLD build" sentences are gone. |
| **R18-4** docs | **DONE** | Runbook `status:` line replaced (v1.17); §5.4 coexistence explanation and pre-build (a) replaced by the landed refusal (`699638fbe`); the decision document's G6 row (and §0 items 8–9) replaced, not appended; the tool intro's G6 text already corrected. |

## Not done / not claimed
- **The official pre-S-L1 capture has not been taken** (the steward runs it under the owner's credentials in the hour before S-L1). The earlier trial's data sha256 `ef8a820d…` is SUPERSEDED (the format changed); the trial under this tool printed data sha256 `d6a9b80d…e5d6` (read-only, one transaction, ≈ 5.6 s). An official run should print the same value if L1 has not changed.
- The re-pin tool has still never run against the real SETTLED-1 output. The automatic-deploy behaviour in the checklist preamble is read from source, not observed.
- Nothing merged, nothing queued, no review dispatched, no migration applied, no production build run, no database write credential used.
