---
artifact: P4_RETIREMENT_PRECENSUS
canonical_id: P4_RETIREMENT_PRECENSUS
version: 1.0
status: CURRENT — pre-census, produced BEFORE P4-A's redirects landed. NOT a deletion warrant.
role: >
  The inbound inventory, candidate condemned tree, cross-campaign import check, and re-runnable
  census methodology that the P4-B deletion warrant (charter §10.3 precondition 1) depends on.
  Produced by the P4 retirement SCOUT during the Paripraśna P3+P4 overnight run. Read-only:
  this document and its instrument delete nothing and change no application code.
derived_from_git_head: 07ed2433f2bce8d658f76169a0a99ac9e0294bfb
census_hash: dd5b9d9a9e2b0d9757bb3656d334cd91e02ce23c06c452ac9207dfab63138577
instrument: platform/scripts/governance/p4_retirement_census.py
baseline_data: 00_ARCHITECTURE/briefs/pariprashna_swarm/census/p4_census_baseline_07ed2433f.json
governed_by:
  - PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §6, §9, §10.2, §10.3
  - CLAUDE.md §N.8 (Earned-Signal Principle)
---

# P4 Retirement — Pre-Census

## 0. The one-sentence recommendation

**The retirement train should not open tonight on P4-A as currently specified: a 308 redirect
on `/clients/[id]/consult` creates an infinite redirect loop on the `PARIPRASHNA_ENABLED=false`
path — which is the P3-F auto-rollback path — because `pariprashna/page.tsx` and
`samiksha/page.tsx` both redirect *to* `consult` when that flag is off (§3.1 below).**
Fix that one interaction inside P4-A and the train can open; land P4-A without fixing it and
the night's own rollback is destroyed by the first lane of the retirement.

Everything else below is the material that makes the 6am verifier's job mechanical.

---

## 1. What this document is and is not

DD-4's first precondition requires **a census refreshed AFTER P4-A's redirects landed** —
re-derived from the live post-redirect `main`, hashed, and checked path-by-path against the
deletion diff. That census cannot exist yet; P4-A has not run.

What exists here instead:

| Deliverable | Status |
|---|---|
| The inbound inventory — P4-A's actual specification | §2, complete at `07ed2433f` |
| The candidate condemned tree, leaf-first, with statuses | §4, complete at `07ed2433f` |
| The PARIŚEṢA-RĀTRI cross-campaign import check | §5, **CLEAN**, re-runnable |
| The census methodology, as a runnable hashing instrument | §6 + `p4_retirement_census.py` |
| The three §10.3 refuter questions, pre-answered as far as tonight allows | §7 |

**This is not a warrant.** No path listed here may be deleted on this document's authority.

---

## 2. The inbound inventory — every way the outside world reaches `consult` / `consume`

**24 entries.** Grouped by what P4-A must do with each. Line numbers are at `07ed2433f`.

### 2.1 API callers — 410 + pointer (per §10.2)

| # | Entry | Who calls it | What P4-A must do |
|---|---|---|---|
| I-1 | `POST /api/chat/consult` (`app/api/chat/consult/route.ts`, 1249 lines) | the live engine door | 410 + pointer to `/api/pariprashna` |
| I-2 | `POST /api/chat/consult/continue` | `ConsumeChatV2.tsx:466` **via the consume alias** | 410 + pointer |
| I-3 | `POST /api/chat/consult/regenerate` | `ConsumeChatV2.tsx:402` **via the consume alias** | 410 + pointer |
| I-4 | `GET /api/chat/consult/resume` | `ConsumeChatV2.tsx:1823` **via the consume alias** | 410 + pointer |
| I-5 | `POST/GET /api/chat/consume` | **`ConsumeChatV2.tsx:2249` — the live chat transport** | already 308→consult; becomes 410 + pointer |
| I-6 | `POST/GET /api/chat/consume/continue` | `ConsumeChatV2.tsx:466` | already 308; becomes 410 + pointer |
| I-7 | `POST/GET /api/chat/consume/regenerate` | `ConsumeChatV2.tsx:402` | already 308; becomes 410 + pointer |
| I-8 | `POST/GET /api/chat/consume/resume` | `ConsumeChatV2.tsx:1823` | already 308; becomes 410 + pointer |
| I-9 | `GET /api/consume/suggestions/context` | **nobody — zero callers repo-wide** | 410 + pointer; safe to condemn (§4) |

**Finding I-A (load-bearing, correct this before writing P4-A).** The `consume` API routes are
*already* 308 aliases, landed by an earlier rename (`unit 0a.1`). Their own header comment says
*"Remove after one release cycle once telemetry confirms no traffic on `/api/chat/consume`."*
**That comment is false.** `ConsumeChatV2.tsx:2249` sets the chat transport to
`api: '/api/chat/consume'`, and lines 402/466/1823 fetch the `consume` sub-paths directly. The
application's own primary client is the traffic. P4-A's inventory must treat `consume` as a
**live, high-traffic API surface**, not a residual alias — and the 410 conversion on I-5..I-8
takes the legacy chat UI down at the API layer *the instant it deploys*, before any browser
redirect can move a user. Sequence the page redirect (§2.2) to land with or before the API 410,
or a user mid-turn on the consult page receives a hard 410 instead of a graceful move.

### 2.2 Browser paths — 308 redirect (per §10.2)

| # | Entry | Reached from | What P4-A must do |
|---|---|---|---|
| I-10 | `/clients/[id]/consult` (`page.tsx`, `layout.tsx`, `error.tsx`, `loading.tsx`) | `clients/[id]/page.tsx:127`, `panchang/page.tsx:57` | 308 → `/clients/[id]/pariprashna` |
| I-11 | `/clients/[id]/consult/[conversationId]` | `ChartSwitcher.tsx` (string-built), deep links | 308, conversationId carried or dropped — **decide explicitly** |
| I-12 | `/clients/[id]/consume` | already `permanentRedirect` → consult (`page.tsx:25`) | re-point to `pariprashna` (do not chain two redirects) |
| I-13 | `/clients/[id]/consume/[conversationId]` | already `permanentRedirect` → consult (`page.tsx:14`) | re-point to `pariprashna` |

### 2.3 In-app navigation that must be re-pointed, not redirected

These construct legacy URLs in code. A 308 makes them *work*, but leaves the codebase asserting
a retired surface — and each is a path a `PARIPRASHNA_ENABLED=false` rollback still traverses.

| # | Reference | Line |
|---|---|---|
| I-14 | `clients/[id]/page.tsx` — "Ask anything" CTA → `/consult` | :127 |
| I-15 | `clients/[id]/page.tsx` — recent-conversation links → `/consume/<conv>` | :134 |
| I-16 | `clients/[id]/panchang/page.tsx` — back-to-consult | :57 |
| I-17 | **`clients/[id]/pariprashna/page.tsx` — flag-OFF fallback `redirect(/clients/${id}/consult)`** | **:43** |
| I-18 | **`clients/[id]/samiksha/page.tsx` — flag-OFF fallback `redirect(/clients/${id}/consult)`** | **:28** |
| I-19 | `components/chat/ConversationSidebar.tsx` — `router.push(.../consume)` ×2 + href ×1 | :153, :235, :395 |
| I-20 | `app/panchang/components/{ActionBar,AskMadhavLink,MuhuratResultsList}.tsx` — `router.push(.../consume?…)` | :322, :108, :183 |
| I-21 | `components/nav/ChartSwitcher.tsx` — string-strips `/consult/<conv>` → `/consult` on chart switch | :45–56 |

I-17 and I-18 are the redirect loop. See §3.1.

### 2.4 Non-browser callers — scripts, CI, governance surfaces

| # | Reference | Kind | What P4-A/B must do |
|---|---|---|---|
| I-22 | `platform/scripts/answer_eval.ts:189`, `scripts/cutover/stage1_smoke.ts:172`, `scripts/eval/runner.py:91`, `scripts/retrieval/probe_11c_b.ts:95`, `scripts/pipeline_smoke_audit.py:875` | eval/smoke harnesses POSTing `/api/chat/consume` | repoint or record as knowingly-retired; a 410 silently turns each into a red harness |
| I-23 | `.github/workflows/chat-v2-ci.yml` — `paths:` filter `platform/src/components/consume/**` (:32) and `npx eslint src/components/consume` (:114) | **cron'd CI (`0 2 * * *`)** | deleting the dir makes the eslint step fail on a missing pattern — must be edited in the same PR |
| I-24 | `platform/src/lib/pariprashna/no_leakage/serving_path_manifest.ts:59` — `'src/app/api/chat/consult/route.ts'` | **Paripraśna safety surface** (no-leakage serving-path manifest) | must be updated deliberately; see Finding I-B |

Also present, non-blocking but must not be silently broken:
`platform/scripts/governance/naming_baseline.json` (2 entries + 2 flag keys),
`platform/scripts/governance/earned_signal_allowlist.json` (3 entries),
`platform/src/generated/harvest/e1_declared.json`,
`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:292` (`route: '/api/chat/consult'` in a capability descriptor).

**Finding I-B (§N.8-shaped).** `serving_path_manifest.ts` is the Paripraśna no-leakage scan's
list of paths that serve readers. It names the condemned consult route. If P4-B deletes the
route and the manifest entry is dropped *without* the pariprashna route being added in its
place, the leakage scan keeps returning green over a surface it no longer covers — a signal
with no detector behind it. Whoever edits that file must show the scan failing against a
deliberately leaky pariprashna response before its next green counts.

---

## 3. What I found that P4-A's spec does not currently account for

### 3.1 The rollback-destroying redirect loop (the reason for §0)

```
platform/src/app/clients/[id]/pariprashna/page.tsx:43
    if (!configService.getFlag('PARIPRASHNA_ENABLED')) redirect(`/clients/${id}/consult`)

platform/src/app/clients/[id]/samiksha/page.tsx:28
    if (!configService.getFlag('PARIPRASHNA_ENABLED')) redirect(`/clients/${id}/consult`)
```

P4-A puts a 308 on `/clients/[id]/consult` pointing at `/clients/[id]/pariprashna`. With
`PARIPRASHNA_ENABLED` true, nothing happens — the flag-off branch is dead. With it **false**,
the two redirects close a cycle: `consult → pariprashna → consult → …`, and the browser stops
with `ERR_TOO_MANY_REDIRECTS` on the chart's only chat surface.

`PARIPRASHNA_ENABLED=false` is not a hypothetical state. It is:
- the state the P3-F **auto-rollback** returns the system to, which §0 ruling 2 arms;
- the state every pre-flip deploy is in;
- the state P4-C exists to make unreachable — and P4-C runs *after* P4-B, two lanes later.

So there is a window, opening at P4-A's deploy and closing only at P4-C's, in which the night's
armed rollback lands the product in a redirect loop. Three defensible dispositions, cheapest-to-
undo first:

1. **P4-A deletes the two flag-off fallbacks in the same commit** (point them at `/dashboard`,
   or drop the guard where the flag is already unconditionally on). Cheap, reversible, keeps the
   train's shape.
2. **P4-A's redirect is made conditional on the flag** (`if flag → 308`, else serve the legacy
   page). Preserves rollback exactly; costs one branch that P4-C then deletes.
3. **Park P4-A until after P4-C's deflagging** — inverts §10.4's strict A→B→C→D serialization
   and is the most expensive to undo. Not recommended.

I did not implement any of them: choosing is the surrogate's call, not the scout's.

### 3.2 Capability the deletion would silently remove

Three modules become orphaned when the consult route dies, and **the Paripraśna engine imports
none of them**. Each is a capability the legacy door had and the new door does not:

| Module | Sole importer | What is lost |
|---|---|---|
| `platform/src/lib/audit/consumer.ts` | `api/chat/consult/route.ts` | the synthesis **audit-log write path** (`writeAuditLog`, validator + tool-call records) |
| `platform/src/lib/ppl/prediction_writer.ts` | `components/chat/PredictionLogModal.tsx` | the **prediction-ledger write** from the reading surface |
| `platform/src/lib/models/openai.ts` | `lib/models/resolver.ts` (legacy branch only) | the OpenAI provider leg |

The import graph is correct that these become dead. That is exactly why they deserve a decision
rather than a deletion: "no importer" here means "the replacement never wired it", not "nobody
needed it". `prediction_writer` in particular is the ledger P4-G's window-opening ask is
supposed to write into. **Filed as a finding; all three are marked AMBIGUOUS and survive.**

### 3.3 A DB-level residue P4-C must NOT touch tonight

`platform/migrations/001_baseline.sql:233` — `conversations.module TEXT NOT NULL CHECK (module
IN ('build','consume'))`, and `:869` — `CHECK (source IN ('consume','eval'))`. Both consult
pages write `module: 'consume'` rows (`consult/page.tsx:121`,
`consult/[conversationId]/page.tsx:53`). Renaming the enum value is a **destructive migration**
and is banned tonight (§9). P4-C's residue sweep is "what grep finds, nothing more" — this is
schema, not residue. Leave it; file it for a later expand-then-contract.

---

## 4. The candidate condemned tree (the pre-census)

Full machine-readable rows — importers, imports, dynamic refs, leaf depth, per-path reason —
are in `census/p4_census_baseline_07ed2433f.json`. Summary:

| Status | Count |
|---|---|
| SURVIVES | **398** |
| AMBIGUOUS (= OUT tonight) | **75** |
| CONDEMNED-CANDIDATE | **8** |

Reachable-from-condemned-entrypoints total: 481 files. `census_hash`
`dd5b9d9a9e2b0d9757bb3656d334cd91e02ce23c06c452ac9207dfab63138577` at `07ed2433f`.

### 4.1 CONDEMNED-CANDIDATE — leaf-first

| Order | Path | Why condemnable |
|---|---|---|
| d0 | `platform/src/app/clients/[id]/consult/loading.tsx` | no importer, no dynamic ref |
| d0 | `platform/src/app/clients/[id]/consume/page.tsx` | redirect stub superseded by P4-A |
| d0 | `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` | redirect stub superseded by P4-A |
| d0 | `platform/src/components/consume/SharedConsumeError.tsx` | only the two consult `error.tsx` import it |
| d1 | `platform/src/app/clients/[id]/consult/error.tsx` | imports only condemned |
| d1 | `platform/src/app/clients/[id]/consult/[conversationId]/error.tsx` | imports only condemned |
| d9 | `platform/src/app/api/consume/suggestions/context/route.ts` | **zero callers repo-wide** |
| d9 | `platform/src/app/clients/[id]/consult/__tests__/consult_page_reports_tolerance.test.ts` | tests only condemned pages |

That is deliberately, honestly small. It is 8 files, not the ~50 a naive walk produces, because
of the rule below.

### 4.2 The ambiguity rule, and what "ambiguous" actually looked like

**AMBIGUOUS = OUT.** 75 paths survive tonight on ambiguity. Three distinct shapes:

**(a) Dynamic / string / config reference (7 paths).** The class a static import walk misses.
`api/chat/consult/route.ts` is the archetype: **zero** remaining production importers, and
**nine** non-import references — `earned_signal_allowlist.json`, `naming_baseline.json`,
`api/mcp/prashna_ask/route.ts`, `api/pariprashna/route.ts`, `generated/harvest/e1_declared.json`,
`lib/pariprashna/injection/index.ts`, `lib/pariprashna/no_leakage/serving_path_manifest.ts`,
`lib/pipeline/cost_caps.ts`, `lib/pipeline/prashna_ask_synthesis.ts`. A graph-only census calls
this file deletable. It is not: two of those nine are governance gates that would go green over
nothing, and one is a Paripraśna safety manifest (Finding I-B).

**(b) Test-only importers remain (31 paths).** `ConsumeChat.tsx`, `ConsumeChatV2.tsx`,
`ConversationSidebarV2.tsx`, `TraceDrawer.tsx`, `SettingsDropdown.tsx`, the whole
`lib/validators/*` leg, and more. The production graph says dead; a test still imports them.
Deleting the file without dispositioning its test is how a deletion PR turns red at merge.
The census reports a **projection** — `projection_tests_codeleted` in the JSON, 14 co-deletable
test files identified — but does **not** adopt it. Co-deleting a test is a decision a verifier
records, not a derivation a script issues.

**(c) Transitivity (the rest).** A CONDEMNED child of an AMBIGUOUS parent would be deleted out
from under a file that is *not* being deleted tonight — the orphaned-importer defect the warrant
exists to prevent, manufactured by the census itself. AMBIGUOUS propagates **down** the graph to
fixpoint. This single rule moved 37 paths out of the condemned set. Every one of them was a file
a graph-only census would have deleted.

### 4.3 Three defects found in the census instrument itself

Recorded because each is a way a future census could be wrong in the unrecoverable direction:

1. **Multi-line imports were not matched.** The first import regex required `from '...'` on the
   same line as `import`. Every `import {\n a,\n b,\n} from '@/x'` was invisible — which
   under-counts the **live** set and therefore **over-condemns**. Fixing it moved 34 files to
   SURVIVES, including `components/ui/dialog.tsx` (imported by three auth modals) and
   `lib/providers/google/cached_content.ts` (imported by the shared pipeline Paripraśna uses).
   Both had been classified CONDEMNED-CANDIDATE.
2. **The cross-campaign check was scoped to the reachable set, not the delete set.** It reported
   **312** "collisions" — every PARIŚEṢA import of `components/ui/button`,
   `lib/auth/authorizeChartAccess`, `lib/adapters/run_adapter`. All noise, all on files the
   census already said SURVIVES. A check that parks the train on noise every time trains the
   operator to ignore it, which is the failure mode the check exists to prevent. Now scoped to
   static imports, from PARIŚEṢA **production** files, into **CONDEMNED-CANDIDATE** paths only.
3. **No transitivity closure** (§4.2c).

None of these were visible from reading the output; each surfaced only from spot-checking a
surprising verdict against the file. **The 6am verifier should spot-check at least three
surprising verdicts by hand before trusting any refreshed census, including one this instrument
calls SURVIVES.**

### 4.4 The riskiest single deletion candidate

`platform/src/app/api/consume/suggestions/context/route.ts`.

It is the only *route* in the CONDEMNED-CANDIDATE list with no redirect stub replacing it, and
it is condemned on the strongest possible internal evidence — grep finds **zero** callers
anywhere in `platform/src`, `platform/tests`, `platform-mcp`, or `platform/scripts`. That is
also precisely why it is the riskiest: it is an *HTTP endpoint*, and the census's entire
evidence base is the repository. A repo-wide grep cannot see a caller that is a deployed client
bundle from an older revision, a bookmark, a browser extension, or an external integration. For
every other candidate the import graph is the whole truth; for this one the graph is silent by
construction and the silence is being read as a verdict. Its `410 + pointer` under P4-A is
strictly more informative than its deletion under P4-B — an API caller that still exists learns
where to go instead of getting a 404. **Recommend: 410 it in P4-A, and let it sit one cycle
behind that 410 rather than deleting it in P4-B.** Cost of being wrong toward survival: one dead
file. Cost of being wrong toward deletion: an unexplained 404 nobody can attribute.

---

## 5. The cross-campaign import check — §10.3's train-parker

**VERDICT: CLEAN.** No PARIŚEṢA-RĀTRI production file statically imports any path in the
condemned-candidate set.

**Territory determination.** Computed live from git rather than assumed: every commit on
`origin/main` since 2026-08-01 whose message matches `parisesa` (case-insensitive), unioned with
the campaign's declared prefixes (`platform-mcp/**`, `platform/python-sidecar/**`,
`platform/src/app/api/mcp/**`, `platform/src/app/api/pariprashna/**`,
`platform/tests/pariprashna/**`, `00_ARCHITECTURE/briefs/parisesa/**`). **662 files**, from
**100 commits** since 2026-08-01 — this campaign is unambiguously live.

**The overlap, stated plainly.** PARIŚEṢA's entire `platform/src/app` footprint is 14 files:
twelve under `api/mcp/**` (SF-003/SF-004 OAuth, db/query, primitives, rate-limit, recent, trace,
asset), plus `api/pariprashna/route.ts` and `settings/personas/PersonaForm.tsx`. Plus one
component, `components/chat/ModelStylePicker.tsx`. **None of the 18 condemned entrypoint files,
and none of the 8 condemned candidates, is in PARIŚEṢA territory.** The two campaigns' file
territories are disjoint, exactly as §10.4 designed.

**The homograph that would have caused the collision.**
`platform/src/app/api/mcp/oauth/codes/consume/route.ts` matches every naive `consume` glob and
is **active PARIŚEṢA territory** (SF-003 PKCE, SF-004 redirect_uri binding, both landed within
the last week). It is OAuth *authorization-code* consumption — an unrelated verb sense of the
same English word. It is excluded by an explicit `NEVER_CONDEMNED` prefix, and the instrument
carries a guard (`homograph_guard`) that enumerates all 65 name-matching paths, shows which 18
are condemned and which 47 are excluded, and **fails** the moment anyone broadens the entrypoint
list toward a `**/consume/**` glob. This is the single most likely way a rushed 6am census
deletes under another campaign's feet.

**Advisory tier (does not park the train, but must be read).** The instrument separately reports
`advisory_hits`: string/config references and test-file references from PARIŚEṢA territory into
the condemned or ambiguous sets. The two that matter are already carried as I-24 / Finding I-B
(`lib/pariprashna/no_leakage/serving_path_manifest.ts`) and §4.2a
(`api/mcp/prashna_ask/route.ts`, `api/pariprashna/route.ts`,
`lib/pipeline/prashna_ask_synthesis.ts` — all documentation-comment references to the consult
route as the fork origin / comparison baseline — plus 5 entries in
`scripts/governance/naming_baseline.json`). **9 advisory hits, 0 blocking.** None is an import.
None parks.

**This check must be re-run, not inherited.** PARIŚEṢA-RĀTRI-V4 may land more commits tonight.
The verdict above is true at `07ed2433f` and at no other commit. The re-run recomputes territory
from git, so a PARIŚEṢA commit landed at 4am is automatically in scope.

---

## 6. The methodology — one command at 6am

```bash
# In a worktree off the POST-REDIRECT main. Never the shared checkout (X-4).
cd <worktree>
git --no-optional-locks fetch origin
git --no-optional-locks reset --hard origin/main          # or: worktree add off origin/main
git --no-optional-locks log -1 --format=%H origin/main    # record this; it must equal the
                                                          # tip the deletion PR is based on

python3 platform/scripts/governance/p4_retirement_census.py \
    --repo-root . \
    --selftest \
    --out /tmp/p4_census_refreshed.json
```

Prints `census_hash`, `git_head`, `counts`, and the cross-campaign verdict. Runtime ~6s.
Exit 3 = the §N.8 selftest failed and **the census is not a detector** — do not delete.

Then, path-by-path against the deletion diff:

```bash
git --no-optional-locks diff --name-status origin/main...HEAD \
  | awk '$1=="D"{print $2}' | sort > /tmp/diff_deleted.txt

python3 -c "
import json,sys
c=json.load(open('/tmp/p4_census_refreshed.json'))
ok={r['path'] for r in c['rows'] if r['status']=='CONDEMNED-CANDIDATE'}
d=set(open('/tmp/diff_deleted.txt').read().split())
extra=sorted(d-ok)
print('census_hash', c['census_hash']); print('git_head   ', c['git_head'])
print('cross_campaign:', c['cross_campaign_check']['verdict'])
print('deleted-but-not-condemned:', len(extra))
[print('  EXTRA', p) for p in extra]
sys.exit(1 if extra or c['cross_campaign_check']['blocking_hits'] else 0)
"
```

**Non-zero exit = the warrant fails and the whole train parks** (§9: *"one extra path fails the
warrant"*). The census's `git_head` must equal the tip the deletion PR is based on; a census
from an earlier fetch is not a census (§9: *"never delete with a census older than the fetch
that precedes the deletion PR"*).

### 6.1 What the instrument does, and its honest limits

Read-only. Walks static imports (`import`/`export…from`, dynamic `import()`, `require()`,
`vi.mock()`), resolves `@/*` → `platform/src/*` and relative + index forms, computes reachability
from the condemned entrypoints and separately from **every surviving** route/page/layout/
middleware/MCP-tool/script, then classifies. Then: transitivity closure to fixpoint → homograph
guard → cross-campaign check → hash over sorted `(path, status)` pairs plus `git_head`.

**§N.8 — how its own green can read false.** `--selftest` requires the corpus to contain BOTH a
real file the classifier calls SURVIVES *because* something outside the condemned set imports it,
AND a real file it calls CONDEMNED. If either discriminator is absent the selftest fails with
exit 3: a classifier with no discriminating case is not a detector, and its greens are vacuous.
At `07ed2433f` both exist (`components/brand/Logo.tsx` ← three surviving pages;
`api/consume/suggestions/context/route.ts` ← nothing).

**Limits, stated rather than hidden.** It cannot see: a caller outside this repository (§4.4); a
route reached only by a deployed older client bundle; a reference built by string concatenation
it cannot constant-fold; a runtime registry keyed by a value computed at import time. It also
cannot substitute for the build (§7.3). Its output is **input to a human line-by-line review**,
which is what DD-4 actually requires — never a replacement for one.

---

## 7. The three §10.3 refuter questions, pre-answered

### 7.1 "Can any deleted path still be reached?"

**Established now.** Every in-repo inbound path is enumerated in §2 (24 entries). Of the 8
condemned candidates: 6 have no in-repo reference of any kind; 1 is a test of the other
condemned pages; 1 (`api/consume/suggestions/context`) is an HTTP endpoint with zero in-repo
callers — and §4.4 argues that its *reachability* is precisely what a repo census cannot settle.

**Must wait for post-redirect state.** Whether P4-A's own redirect targets resolve; whether the
redirect chain is 1 hop (correct) or 2 (`consume → consult → pariprashna`, which I-12/I-13 will
produce if `consume` is left pointing at `consult`); and the §3.1 loop, which is only observable
with `PARIPRASHNA_ENABLED=false`. **Add to the P4-A close probe set: one browser observation
with the flag OFF.** Per DD-21 that must be observed, not reasoned about — and it is the one
observation that catches the night's worst available outcome.

### 7.2 "Does any test, migration, or cron reference it?"

**YES on all three. Established now, and none of it clears without an edit.**

- **Tests:** 31 of the 75 AMBIGUOUS paths are ambiguous *solely* because a test still imports
  them (§4.2b); another 37 are ambiguous only because they are imported by one of those 31. 14
  test files are identified as co-deletable; the rest need repointing. This is the bulk of P4-B's
  actual work, and it is where the condemned set grows from 8 once the decisions are recorded.
- **Cron:** `.github/workflows/chat-v2-ci.yml` runs `0 2 * * *` and both filters on
  (`:32`) and eslints (`:114`) `platform/src/components/consume/**`. Delete the directory
  without editing the workflow and the nightly job fails on a missing pattern.
- **Migration/schema:** `001_baseline.sql:233` `CHECK (module IN ('build','consume'))` and
  `:869` `CHECK (source IN ('consume','eval'))`. **Out of scope tonight** — changing them is a
  destructive migration (§9), and they are schema, not residue (§3.3).

### 7.3 "Does the build prove zero orphaned importers?"

**Cannot be established now, and this is not a limitation to work around.** The build proof is
`npx tsc --noEmit` + `next build` **against the post-deletion tree**; no tree with the deletions
in it exists yet. This worktree has no `node_modules`, so the command must run in the installed
checkout or a CI job.

What §7.3 will require at 6am:

```bash
cd platform && npx tsc --noEmit && npm run lint && npm run build
```

Two disciplines that make this a real proof rather than a green:
1. **Run it on the base commit first.** A build that was already red before the deletion proves
   nothing about the deletion. Baseline green, then delete, then green again.
2. **`tsc --noEmit` alone is not sufficient** for this repo. 37 test files reach their subject
   via `readFileSync(…'/src/app/api/chat/consult/route.ts')` and assert on source *text*, not via
   imports — TypeScript will never see them, and neither will an import-graph census. `npm test` must run too, and a `MODULE_NOT
   _FOUND`/`ENOENT` there is exactly the orphan the build cannot detect.

---

## 8. Ledger of what this document changed

Nothing in application code. Two files added on branch `pariprashna/p4-census`:
`platform/scripts/governance/p4_retirement_census.py` (read-only instrument) and
`census/p4_census_baseline_07ed2433f.json` (this census's data), plus this document.
No path was deleted. No PARIŚEṢA file was read for anything other than an import check, and none
was modified.
