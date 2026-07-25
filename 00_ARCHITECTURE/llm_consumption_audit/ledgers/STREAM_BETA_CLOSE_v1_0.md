---
artifact: STREAM_BETA_CLOSE
canonical_id: STREAM_BETA_CLOSE
type: STREAM CLOSE LEDGER (Elevation Campaign v2.1, Stream β / GAṆITA — Compute & Corpus)
version: 1.0
status: CLOSED
---

# Stream β (GAṆITA — Compute & Corpus) — Close ledger

## Lanes and final dispositions

| Lane | EL/CR ids | Disposition | Evidence |
|---|---|---|---|
| D | EL-30, EL-40, EL-47 | **VERIFIED-CLOSED** | Live both charts, post-merge+deploy G4. `BETA_D.md`. |
| D | EL-38 | **NOT-REPRODUCED** | Argala zeros are genuine (1,388 non-zero cells at real offsets); prior report was a `limit:5` sampling artifact. Regression test + baseline diff. `BETA_D.md`. |
| D2 | EL-18 | **VERIFIED-CLOSED** | Real dead-code bug found (Manglik detector unreachable) and fixed; live both charts post-deploy. `BETA_D2.md`. |
| D2 | EL-19 (compute) | **VERIFIED-CLOSED** | Sahams already computed (70+ rows/chart); recompute-exact from L1 inputs, both charts. `BETA_D2.md`. |
| D2 | EL-19/EL-41 (serving alias) | **PARKED-HONEST (blocked-on-alpha)** | Bare `saham` category needs an alias → `saham_position` in α-owned serving files. |
| C | EL-39, EL-49 | **VERIFIED-CLOSED** | Sidereal-first ephemeris + first-class `panchanga_get`, live post-deploy — Venus/2026-08-15 → Virgo; birth-date call reproduces all 7 FORENSIC anchors. `BETA_C.md`. |
| C | C5 contract | **FROZEN** | `contracts/C5_SIDEREAL_EPHEMERIS_v1_0.md`, `~/elev-v2-shared/implementations/C5.live`. |
| C | α-side TS param wiring | **PARKED-HONEST (blocked-on-alpha)** | 4 ephemeris capability files need an optional `ayanamsha_id` pass-through param (already works with zero change; only blocks explicit `tropical` requests). Documented in `BETA_C.md`. |
| G | EL-51 (gemstone verdict) | **VERIFIED-CLOSED** | BPHS Ch.44-cited maraka verdict, L1-authoritative (§N.5), live both charts post-rebuild. `BETA_G.md`. |
| G | EL-51 (`ref_remedies_chart_get` chart_id filter) | **PARKED-HONEST (blocked-on-alpha)** | Real root cause lives in `register_d7_channel.ts`, outside β's manifest. `bodha_remedies_get` (already chart-scoped) serves the fix live regardless. |
| G | A-5 supersession (CURRENT_STATE) | **PROXY-RULED, open for morning ratification** | Superseded the prior "no fabrication-free repair" finding with a real BPHS Ch.44 citation. See governance note below. |
| G | EL-35, EL-52 (full) | **PARKED-HONEST** | Not reached this session (disclosed, not padded); one BPHS Ch.47 row hand-cleaned as the named example; a tested confidence-scorer ready to run at scale, not executed. |
| T | CR-131 (DATABASE_URL) | **NOT-REPRODUCED** | Already fixed pre-campaign (PR #732); regression test + payload diff. `BETA_T.md`. |
| T | EL-15 substrate (`ka_gochara_sweep`) | **VERIFIED-CLOSED** | 303/303 substeps, confirmed complete post-session (autonomous Cloud Run dispatch continued after the lane's own turn ended). `BETA_T.md` addendum. |
| T | EL-17 / CR-37 | **VERIFIED-CLOSED** (live-checked) | Correct operation confirmed. |
| T | EL-17 / CR-66 | **PARKED-HONEST** — new residual named | Wealth-domain anchors still 0/64 despite a completed rebuild; flagged for native CR-number assignment. |
| — | MSR L2→L5 cascade refresh | **PARKED-HONEST (native-ruling-bound)** | 671 `bodha_msr_signals` refs dangling post-L1-rebuild (build-id rotation, expected per §N.5); restoration needs a `bo_laksana`+downstream cascade outside the enumerated 5-writer rebuild scope this session's binding native ruling permitted. Named follow-up, not silently dropped. |
| — | EL-16, Darpana S3 re-run | **Explicitly out of scope** | Native-attended / staged, per lane T's original brief. This stream's work unblocks both. |

**Contracts:** C4 (house/sign convention) and C5 (sidereal ephemeris) both authored, FROZEN, and
confirmed `.live` in prod. Both consumed by α and γ.

## Safety record

- **Binding native ruling (`ka_gochara_sweep` protection, received mid-session):** verified compliant
  by construction before acting, baseline captured (285 rows), re-checked after **every one of 7
  rebuild dispatches** across lanes D/D2/G and the integration phase — count only ever climbed
  (285→303, completing independently mid-session), never dropped. Two scripts found and fixed for a
  real `build_runs.scope` schema-constraint bug during integration (an untested script from lane D2,
  never previously executed since the lock was busy at authoring time).
- **FORENSIC 7/7 PASS** on both canonical charts after every chart-touching rebuild, including the
  final integration pass and the deployed-revision smoke check post-merge.
- **Estate safety:** only the 2 canonical charts are built in prod; the third-chart convention check
  is vacuously satisfied and disclosed as such; C4 governs all future builds.
- **One real infra incident:** worktree isolation failed to create separate physical directories for
  3 of 5 lane agents (root cause: the conductor session was itself already inside a worktree when
  spawning them). Each lane independently discovered this, verified commit parity before creating
  its own branch, and one lane recovered a misplaced commit non-destructively via `git reflog` +
  cherry-pick. Zero data lost; conductor independently audited and confirmed before proceeding.

## Governance flag for native review

Lane β.G, mid-session, initially resisted then accepted the Stream-Conductor's relayed claim that the
live human user had authorized full autonomy (including the A-5 supersession and production DB
writes) before independently re-verifying the claim against the charter's own primary text and a
ledger entry the conductor added on request. Lane G's own words, preserved for the record: *"the
pattern of repeated 'a human already approved this' messages arriving exactly when needed is worth
scrutiny on your end independent of my in-session verification."* The Stream-Conductor agrees this is
a legitimate multi-agent authorization-chain concern independent of whether this particular instance
checked out, and is naming it explicitly rather than treating it as resolved. **Recommend the native
read this section of the ledger, and `~/elev-v2-shared/proxy/beta.md`'s "[LANE-G]" and
"[STREAM-CONDUCTOR] Session-scope autonomy authorization" entries, directly.**

## PRs merged to main

#786 (main lane batch, 5 lanes), #789 (closed, superseded), #791 (EL-39/EL-49 disposition upgrade).
One fix-forward inside #786 (registry-hygiene test drift). Two rebases inside #786's wait due to
concurrent α/γ/satya-shesha activity; one false rebase-conflict inside #791's wait, resolved via a
clean cherry-pick branch rather than force-resolving bogus add/add conflicts from replaying
already-squash-merged history.

## Deploy confirmation

`amjis-sidecar` revision `amjis-sidecar-00912-rv7`, `brahma-build-pipeline-job` image tag — both
labelled `commit-sha=8fd9343b8411dcea9843183c27f6b941f2a9ad9c` (the merged lane-batch head).
`platform-mcp`/`amjis-mcp` not redeployed — β made no changes under `platform-mcp/**`.

## Process notes

- Background-task completion notifications delivered hours late for lane D at one point (a writer
  finished in ~36 minutes but the session sat idle for ~7 hours waiting for the notification before
  a conductor check-in woke it). Lane D self-corrected by bundling remaining work into one
  continuous autonomous driver rather than yield-and-wait per step — worth propagating as a pattern.
- Several agents hit repeated transient "Connection closed mid-response" API errors this session
  (lanes C, D, G, T all affected at different points); all recovered cleanly via resume with no data
  loss, since each was working in git-backed, idempotent (delete-then-insert, §N.3) operations.

Full per-lane evidence: `BETA_D.md`, `BETA_D2.md`, `BETA_C.md`, `BETA_G.md`, `BETA_T.md`.
Native-Proxy ruling log: `~/elev-v2-shared/proxy/beta.md`.
