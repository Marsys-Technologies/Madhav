# Domain G — Cross-Campaign Safety

Audited read-only on branch `l3/kala-readiness-audit`, repo `/Users/Dev/madhav-l3/audit`, 2026-09-22.

## What was checked (with exact reproducing command for each)

1. **Pūrṇa territory markers**
   `grep -rli "pariprashna\|beyond_acarya\|pūrṇa\|purna_anveshana" --include="*.md" --include="*.json" --include="*.py" --include="*.ts" .`
   `find . -iname "*BEYOND_ACARYA_ACCEPTANCE*" -o -iname "*pariprashna*"`

2. **Lease protocol on `origin/campaign-coordination`**
   `git fetch origin campaign-coordination:refs/remotes/origin/campaign-coordination`
   `git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`
   `git log origin/campaign-coordination -5 --oneline`
   `git log origin/campaign-coordination -1 --format="%H %ad" --date=iso`

3. **Shared surfaces / partition rules**
   `sed -n '235,262p' 00_ARCHITECTURE/briefs/nirmana/MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` (§3.3/§3.4)

4. **`L3-REQ`/`PA-REQ` interlock**
   `grep -rn "L3-REQ\|PA-REQ" --include="*.md" .`

5. **SCU→`ka_*` acceptance dependency**
   `grep -n "SCU (" -i 00_ARCHITECTURE/briefs/nirmana/*.md`
   `grep -rn "ka_gochara\|ka_bhavishya_lekha\|ka_dasha_kala\|ka_yojaka\|ka_kalasutra\|ka_kshetra" platform/src/lib/retrieval/registry/knowledge/*.ts`
   `Read platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts:3070-3170`

## Findings

### 1. Pūrṇa's territory and cadence

Pūrṇa Anveṣaṇa ("beyond-ācārya", internal name Pariprashna) owns a large, well-marked
surface disjoint from L3:
- `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v{1..5}.json` — its
  acceptance-record history.
- `platform/src/lib/vidhi/inquiry/beyond_acarya_acceptance.ts` (+ `.corpus.ts`, `.test.ts`) —
  the acceptance logic itself.
- `platform/tests/pariprashna/**` including `platform/tests/pariprashna/route_ports/baseline/*.json`
  (canary fixtures: `1-byte-trickle.json`, `3s-stall.json`, `disconnect-mid-block.json`,
  `single-pass.json`, `branch-existing-conversation.json`) — must not be touched by L3 or this
  audit.
- `platform/src/app/api/pariprashna/**`, `platform/src/components/pariprashna/**`,
  `platform/src/lib/pariprashna/**` — its serving surface.
- `.github/workflows/pariprashna-ci.yml`, `pariprashna-post-deploy-smoke.yml`.

**Cadence — event-driven, not fixed-interval.** `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`
line ~165: "pipeline image rebuild is path-gated on `diff(deployed-image-sha..HEAD)` ∩
`PIPELINE_PATTERN`" and "routine migrate runs on every push." Deploys/rebuilds are triggered by
CI on push to protected `main`, not on a clock. The only documented time-based cadence is
reporting, not execution: line ~405, "Each campaign updates its own state file at milestones;
the strategy session reads both plus Cloud Run **at least daily** during Phase 0/1." No
automated cron/scheduled Pūrṇa rebuild was found — COULD NOT VERIFY a fixed rebuild interval
beyond this "at least daily human/strategy-session check" convention; did not find a
`.github/workflows/*.yml` with a `schedule:` trigger tied to Pūrṇa specifically (tried grepping
workflow filenames and the plan doc; two reasonable attempts, moving on).

### 2. Lease protocol on `origin/campaign-coordination`

File: `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on branch `campaign-coordination`
(unprotected, directly pushable by both campaigns — deliberately faster than `main`, which is
protected and can lag by minutes).

**Format.** A markdown table under `## 1. DEPLOY/REBUILD LEASE (prime rule)` with columns:
`# (lease id) | campaign | purpose (free text) | started (IST) | expiry (IST) | status`.
New rows are prepended (most recent lease is the topmost data row).

**Claim/release mechanics.** Documented procedure (verbatim from §0 of the file):
```
cd <your own worktree>            # never the main checkout
git fetch origin campaign-coordination
git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
# read §1 lease table; if the other campaign holds an ACTIVE, unexpired lease: WAIT.
# to claim/release: edit the file on a local checkout of campaign-coordination and
git push origin HEAD:campaign-coordination
```
If the push is rejected non-fast-forward, another campaign wrote concurrently — fetch, re-read,
re-apply, push again. This is optimistic-concurrency-by-git, not a real lock: there is no
atomic claim primitive, only "push and hope," with the non-fast-forward rejection as the only
collision guard.

**"ACTIVE unexpired lease" — mechanically, this is NOT an automated check.** The rule text says
"A lease past its stated expiry is DEAD: the other campaign may proceed after appending an
OVERRIDE note citing the expiry" — i.e. expiry is enforced entirely by the *next reader*
manually comparing the `expiry (IST)` column against wall-clock time. Nothing in the repo
flips a stale row's `status` field automatically. **This is empirically confirmed, not just
inferred from the prose**: the live table (as fetched) contains at least five rows whose
`status` still literally reads `ACTIVE` (e.g. `MADHAV-PURNA-DELIVERY-ORCHESTRATION-SUCCESSOR-20260919`,
expiry `2026-09-19 23:30 IST`; `MADHAV-PURNA-DELIVERY-BACKLOG-SUCCESSOR-20260919`, expiry
`2026-09-19 22:30 IST`; `MADHAV-PURNA-DELIVERY-ACL-CLEANUP-20260919`, expiry `2026-09-19 21:30 IST`;
`MADHAV-PURNA-DELIVERY-SCHEMA-SUCCESSOR-20260919`, expiry `2026-09-19 21:00 IST`;
`MADHAV-PURNA-DELIVERY-REPAIR-SUCCESSOR-20260919`, expiry `2026-09-19 20:15 IST`;
`MADHAV-PURNA-DELIVERY-REPAIR-20260919`, expiry `2026-09-19 19:30 IST`) even though the file's
own newer rows show they were superseded hours later on the same day, and it is now 2026-09-22.
**Any tool or agent that greps this file for the literal string `ACTIVE` without also parsing
and comparing the expiry timestamp will misread these six rows as currently-held leases when
they are not.** This is a real, demonstrated risk in the coordination mechanism, not a
hypothetical one.

**Currently held lease (as of last fetch, 2026-09-22).** The topmost (most recent) row is
`MADHAV-L3-KALA-W1-DISPATCH-20260920` (L3 Kāla / Claude Code), started 2026-09-20 04:16 IST,
expiry 05:16 IST, **status RELEASED** — the dispatch itself failed structurally
(`psycopg.errors.InsufficientPrivilege`: the `data_plane_builder` identity has zero role
memberships / no grant on `asset_registry`), confirmed by direct privilege introspection, not
inferred; no partial write occurred. Immediately below it, `MADHAV-PURNA-DELIVERY-DATA-PLANE-
ALLOWLIST-SUCCESSOR-20260920` (Pūrṇa/Codex) is also **RELEASED** (2026-09-20 01:50 IST). Latest
commit on `origin/campaign-coordination` is `6296d7484` at 2026-09-20 04:31:59 +0530 — **the
coordination branch itself has not been touched in ~2.5 days relative to the stated "today" of
2026-09-22**, i.e. no lease claim/release activity by either campaign since the L3 W1 dispatch
failure. **No lease is currently ACTIVE by either campaign** (by timestamp reading, not by
trusting the stale `status` strings above).

### 3. Shared surfaces

Per `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §3.3, five shared surfaces with per-surface
partition rules:
1. **Production mutation** (migration apply, cutover dispatch, orchestrator build/rebuild of
   shared-table assets, traffic promotion) — serialized via the lease table above; PR merges,
   CI, and disposable-DB work are explicitly NOT leased.
2. **Migration numbering** — partitioned by range, no lease needed: Pūrṇa **1042–1069**, L3
   **1070–1119**, cross-cutting **1120+** by logged request.
3. **Generated artifacts** (`src/generated/*`, e.g. `capability_knowledge.snapshot.json`) —
   regenerate-never-hand-edit; merge-race loser rebases and reruns the generators
   (`npm run codegen:capability-estate-census`, `codegen:capability-knowledge`, writer-digest
   generator, `nirmana_analysis_layer_pins.py`).
4. **`platform/src/lib/retrieval/registry/layers/L3_kala/**`** — the one real source overlap.
   L3 owns the directory; Pūrṇa may only touch availability-contract/metadata that *references*
   L3 handlers, never handler semantics — any semantic change is an `L3-REQ-nn`, not a Pūrṇa PR.
5. **Asset territory / DB tables** — disjoint by construction (`ka_*`/`kala_*` vs
   `planner_*`/`inquiry_*`). Pūrṇa's own plan §15 forbids it from self-serving a `ka_*` rebuild
   to light an SCU.

Confirmed concretely: `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts`
lines 3097–3100 and 3160–3162 contain live SQL (`build_observation` CTEs) that join
`build_run_assets bra JOIN build_runs br` filtered on `bra.asset_id = 'ka_bhavishya_lekha'` for
the `query_projections` and `query_temporal_activation` availability descriptors — i.e. Pūrṇa's
own served-availability logic directly reads L3's build/asset-state tables. This is the
concrete code-level instance of surface 5's "disjoint tables" claim being bridged deliberately
through availability-contract queries (not writes).

### 4. The `L3-REQ`/`PA-REQ` interlock

Documented at `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §3.4 as "the two explicit
interlocks":
- **I-1 (Pūrṇa → L3 receipt requests).** When a Pūrṇa product case can't reach `live_verified`
  because a `ka_*`-bound SCU lacks an accepted receipt, Pūrṇa records
  `BLOCKED_ON_L3_RECEIPT(<asset_id>)` in its own matrix and appends `L3-REQ-nn` to the
  `CAMPAIGN_COORDINATION.md` §6 LOG naming the asset, SCU, and case ids. L3 orders its frontier
  by this request set but "may not skip an upstream wave to satisfy a request" — this is the
  *only* cross-campaign priority signal.
- **I-2 (L3 → Pūrṇa consumer proof).** L3's `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` status for
  an asset needs a real receiving operator; L3 may use Pūrṇa's three-door collector/judge
  read-only against its own fixtures but may not modify them — a needed collector change is a
  `PA-REQ-nn` in the same LOG.

This is a **documentation/process convention, not a mechanically enforced gate** — it is a
named LOG-entry protocol inside the same manually-edited coordination file as the lease table,
with no CI check found that blocks a PR for missing/ignoring an `L3-REQ`/`PA-REQ` entry. The
migration-number partition (surface 2 above) is the one interlock with an actual mechanical
teeth-equivalent (a numeric range collision would be visible/rejectable at migration-apply
time), but even that is enforced by convention (the stated ranges), not a CI guard verified in
this pass — COULD NOT VERIFY a CI check enforcing the 1042–1069/1070–1119/1120+ migration
number partition; searched workflow files under `.github/workflows/` for "1070" / "1120" and
found none (one grep attempt; did not find a second plausible enforcement location, moving on).

### 5. Does Pūrṇa's live acceptance genuinely depend on L3 receipts?

**Yes — confirmed with a file:line citation, not inferred from prose.**

SCU = **Semantic Capability Unit** (defined at
`00_ARCHITECTURE/briefs/nirmana/MADHAV_PLANNER_CAPABILITY_KNOWLEDGE_AND_INQUIRY_IMPLEMENTATION_v1_0.md`
lines 24 and 76: "Federated Semantic Capability Unit (SCU) declarations live beside the
registry descriptors that own the executable routes" / "## 4. Semantic Capability Unit
contract").

The "23 SCUs bind to `ka_*`" claim traces to `platform/src/generated/capability_knowledge.snapshot.json`
(generated artifact; contains `scu_id` / `target_scu_id` entries, e.g. `scu.kala.temporal_activation`
at line 88, `scu.bodha.mechanism.network` at line 23) plus the editorial-review declarations at:
- `platform/src/lib/retrieval/registry/knowledge/editorial.ts:113` — `ka_kalasutra` /
  `kala_activation` rows, disposition `route_evidence_only` (no reviewed output-digest hash
  joined yet — an honest gap, not a green check).
- `platform/src/lib/retrieval/registry/knowledge/editorial.ts:114` — `ka_yojaka` /
  `kala_activation_predicates`, disposition `reviewed_output`, evidence
  `platform/migrations/1024_nirmana_l3_ka_yojaka_output_digest_spec.sql:80`.
- `platform/src/lib/retrieval/registry/knowledge/editorial.ts:115` — `ka_bhavishya_lekha` /
  `kala_bhavishya forward windows`, disposition `reviewed_output`, evidence
  `platform/migrations/974_nirmana_l3_ka_bhavishya_lekha_output_digest_spec.sql:232`.
- `platform/src/lib/retrieval/registry/knowledge/producer_editorial_review.ts:66,316,341,346,356,361`
  — maps SCU groups to `ka_gochara`, `ka_gochara_v3_century_materialize`, `ka_graha_sancara`,
  `ka_gochara_resonance`, `ka_bhavishya_lekha`, `ka_dasha_kala`, `ka_kalasutra`, `ka_yojaka`,
  `ka_kshetra`.

**The live runtime dependency (the strongest evidence):**
`platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts:3096-3100` (inside
the `query_projections` availability-contract SQL) and `:3160-3162` (inside
`query_temporal_activation`) both contain a `build_observation` CTE:
```sql
SELECT br.id::text AS build_id, br.state AS build_state, bra.state AS asset_state
  FROM build_run_assets bra JOIN build_runs br ON br.id = bra.run_id
 WHERE br.chart_id = $1::uuid AND bra.asset_id = 'ka_bhavishya_lekha'
 ORDER BY COALESCE(bra.ended_at, br.ended_at, br.created_at) DESC LIMIT 0
```
This is compiled into the served availability-contract query for two Pūrṇa-consumed
descriptors and directly reads L3's `build_run_assets`/`build_runs` state keyed on a `ka_*`
asset id — i.e. Pūrṇa's own served-availability logic is structurally coupled to L3's build
state for at least this asset. Combined with the plan's own claim ("the active build has only
one proven `ka_gochara` receipt and lacks current receipts … needed to light the relevant query
SCUs" — `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` line ~127) this substantiates the
dependency direction stated in the brief: **Pūrṇa depends on L3, not the other way round.**

## Verdict: NEEDS DECISION

Not a hard blocker for L3 readiness, but two items need a native/PB-3 decision before L3
resumes production-touching work (builds, migrations, deploys):

1. **Stale `ACTIVE` status rows on `origin/campaign-coordination` are a live misread risk.**
   Six Pūrṇa lease rows from 2026-09-19 still literally say `ACTIVE` in the `status` column
   despite being hours-to-days expired and superseded. Any L3 conductor (human or automated)
   that greps the file for `ACTIVE` rather than parsing+comparing the `expiry (IST)` column
   against wall-clock time could wrongly conclude a Pūrṇa lease is currently held and either
   wait needlessly or — worse — could miss a genuinely active lease if the convention is
   trusted loosely in the other direction. Recommend: before any L3 production action, always
   compute "most recent row by position, read its expiry, compare to `date` in IST" rather than
   string-matching `status`.
2. **The `L3-REQ`/`PA-REQ` interlock and the migration-number partition are process
   conventions with no CI enforcement found.** They rely entirely on both campaigns' conductors
   reading and honoring the same markdown file. This audit did not find a lint/CI gate that
   would catch a violation (e.g., an L3 migration numbered in Pūrṇa's 1042–1069 range, or a
   Pūrṇa PR editing `L3_kala/**` handler semantics without an `L3-REQ` LOG entry). This is
   consistent with the rest of the coordination mechanism (lease claim/release is also
   convention + git non-fast-forward, not a real lock) but is worth flagging explicitly since it
   is the only thing standing between the two campaigns' in-flight work.

No blocking safety defect was found in the mechanism itself (the git non-fast-forward push
guard does provide a real, if coarse, collision check for the lease file's own edits), and the
last actual lease interaction (L3 W1 dispatch, 2026-09-20) was handled correctly per protocol
(checked the Pūrṇa row above it, confirmed RELEASED, claimed narrowly, released with evidence
after a clean failure diagnosis).

## Evidence that could have made this verdict fail

- If any lease row's `status` were `ACTIVE` **and** its `expiry (IST)` were in the future
  relative to 2026-09-22, that would mean a real, currently-held lease by the other campaign —
  this audit would then be READY-only-after-that-lease-clears, or NOT READY if L3 needed to
  mutate production immediately. No such row was found (verified by timestamp comparison, not
  string match — see Finding 2).
- If `source_query_availability.ts` had shown Pūrṇa *writing* to a `ka_*`/`kala_*` table rather
  than only reading `build_run_assets`/`build_runs` state, that would be a direct violation of
  shared-surface rule 5 (disjoint asset territory) — verdict would move to NOT READY pending an
  escalation. Only reads were found.
- If any `.github/workflows/*.yml` had contained a `schedule:` cron trigger for a Pūrṇa
  production rebuild, that would upgrade Finding 1's cadence claim from "event-driven, best
  documented as daily human check" to "mechanically scheduled" — changing the collision-risk
  analysis (a scheduled rebuild is more predictable/avoidable than an ad hoc one). Not found in
  two search attempts; flagged as COULD NOT VERIFY rather than asserted absent with certainty.
