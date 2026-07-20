---
artifact: BIND_PG-2
type: BINDER (opens PG-2 under BRIEF_PG-2.md §B)
version: 1.0
status: OPEN
authored_by: Claude Code (Sonnet 5), conductor session, 2026-07-19
governs: CLAUDECODE_BRIEF_PG2_DIAGNOSTIC_v1_0.md (BRIEF_PG-2 v1.0)
---

# BIND_PG-2 — Wave Open

## B-1 — Base pin (from `origin/main`, fetched)
`git fetch origin main` → `origin/main` @ `4b69df8c510fb3cfa42c9f00b57fcc378dd2f44a`.
`pg2/wave` branch cut via `git worktree add ... -b pg2/wave origin/main` (NOT the
primary checkout, which still holds `pg1/wave` and unrelated concurrent-session
dirty files). This directly applies the brief's correction: PG-1's contamination
traced to branching from local `main`; PG-2 branches from `origin/main` at a clean,
freshly-fetched SHA in its own worktree.

**Substrate note:** `origin/main` at this SHA does not yet contain PG-1's own work
(PR #613 unmerged — see B-2). Since M-1 must audit PG-1's sealed artifacts and Z-2
must correct them, PG-1's artifact files were imported via `git checkout
origin/pg1/wave -- <paths>` (a file-content checkout, not a branch merge — a full
merge would also pull in an unrelated ~50-commit D-3-closeout chain that sits on
`origin/pg1/wave`'s history from local `main` at the time PG-1 branched, discovered
this session while investigating merge conflicts). Committed as `c561bb01`. This
import will need reconciliation once #613 merges to `origin/main` — recorded as a
known follow-up, not deferred silently.

## B-2 — PG-1 PR status
`gh pr view 613` → **state: OPEN, unmerged.** PG-2 bases on `origin/main` per B-1;
`pg2/wave`'s eventual PR will need rebasing once #613 lands (predicted by the brief
itself). Recorded, not treated as a blocker (§0.3 — read-only/diagnostic posture is
safe to run concurrently, same reasoning as PG-1's own B-2 vs D-4a).

## B-3 — Worktree isolation
**Not yet applicable** — no lanes dispatched at BIND time. This slot is the
hard gate verified immediately before SPAWN (§1 step 2), not at BIND. Conductor's
own integration worktree (`pg2/wave` at `/Users/Dev/Vibe-Coding/Apps/Madhav-pg2-wave`)
is itself correctly isolated from the primary checkout. Per-lane worktrees
(`Madhav-pg2-<lane>`, branch `pg2/<lane>`) are created immediately following this
BIND, and `git worktree list` is re-run and recorded before any lane implementer is
dispatched — see `state/STATE_PG-2.md` for the verified list.

## B-4 — Chat-path reachability
**Reachable, auth-gated (expected).** `GET /` → `307` (redirect, presumably to
`/login` — normal Next.js/Firebase-auth behavior). `POST /api/chat/consult`
(no auth, no body) → `401`. This confirms the deployed app is up and the route
exists and enforces auth — it does NOT yet confirm an authenticated call succeeds.
X-2 is responsible for the actual authenticated invocation (mechanism TBD by that
lane — Firebase session token, an existing test/service credential, or browser
automation against the live login flow). **Not parked** — reachability is
confirmed; only the authenticated-call mechanism remains for X-2 to solve.

## B-5 — Baseline `chart_facts` triple (timestamped)
Run once at BIND, this session (exact wall-clock unavailable to this environment;
recorded as "BIND-time, this session," consistent with PG-1's own convention):

| Query | Result |
|---|---|
| `SELECT count(*) FROM chart_facts` (all charts) | **276,206** |
| `SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-...'` (Abhisek) | **138,519** |
| `SELECT chart_id, count(*) FROM chart_facts GROUP BY 1` | `482012f1` (Abhisek) = 138,519; `1c826d5a` (Abhinandan) = 137,687; **only 2 of the 4 charts in the system have any `chart_facts` rows** (Arunima `acdf0d66` and Kiran `cb73cd3d` = 0, presumably unbuilt) |

**This BIND-time probe already resolves H4 (chart conflation) for the
276,206-vs-138,519 pairing: 138,519 + 137,687 = 276,206 exactly.** The
"all-charts" figure is not a conflation artifact — it is the correct sum across
the two charts that have been built. **The genuinely open question narrows to
one number**: why is Abhisek's own chart-scoped count (138,519) ~5.03× the sealed
`L1_GANITA_CLOSURE` canonical figure (27,554)? 138,519 / 27,554 = 5.028 — strikingly
close to 5, consistent with H1 (native's 2026-07-12 per-ayanamsha hypothesis:
"135,645 ≈ 27,554 × ~5 ayanamshas"), though the exact figure has moved between
PG-1's BIND probe (138,519) and this BIND probe (138,519 — **identical**, no
intra-session movement detected THIS TIME, contradicting PG-1's own report of
"unstable across probes" — X-1 must reconcile this: was PG-1's earlier "276,206"
observation actually a *different, unfiltered* query result being compared
apples-to-oranges against a chart-scoped 138,519, rather than genuine instability?
This is now X-1's leading question, refined by this BIND probe).

## B-6 — PG-1 artifact fingerprints (sha256, this exact imported version)
```
e7a4c2d6b71556a86b348ddab7738f85303ea0689ec2fba8e9b4a80fd9616a41  pg1_audit/REPORT_PG-1.md
5b9ba1a8e3e3d07e9e81e0d65b45d7c2644b979135fb14d48e85d312ba49ee79  RETRIEVAL_SYSTEM_TRUTH_v1_0.md
0d33df3f59162a539f517cd57c93f0ca3bdfb65229c21efb84f5de4bb91b67de  PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md
```
M-1's audit targets exactly these versions (as imported into `pg2/wave` at commit
`c561bb01`, sourced from `origin/pg1/wave`).

---

**Binder ruling: brief is BOUND.** No BIND-AT-OPEN slot forces a PARK. B-4 confirms
reachability (not full authenticated success — that's X-2's job). Lanes spawn next,
into isolated worktrees per §4 (hard gate, verified before dispatch, not waived).
