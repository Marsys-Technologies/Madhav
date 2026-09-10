---
artifact: S5_LIVE_REPROOF_CHECKPOINT
version: 1.0
status: CHECKPOINT — NOT A CLOSURE
stream: S5 (Security, Privacy and Data Integrity)
actor: lead-s5
campaign: pariprashna-experience-assurance-v3
date: 2026-08-28
deployed_revision_proven_against: eed62d1bef9285d3271b70c21673f55fce5a2034
cloud_run_revision: amjis-web-01766-ppj
host: https://amjis-web-938361928218.asia-south1.run.app
closure_claimed: false
---

# S5 — Live Re-Proof Pass Checkpoint

This pass converted the merged S5 authorization fixes from "fixed in code" to
"proven fixed on production", gave S3's CRITICAL `V3-E-016` a live verdict, and
surfaced two governance facts the ledger could not otherwise carry.

**No closure is claimed.** All six stream closures are deferred to convergence
(Session C) by native decision.

---

## 0. Two corrections to the briefing, reported rather than complied with

### 0.1 Production is NOT `d4e282d6e`

The brief stated production equals current `main` HEAD at `d4e282d6e`. Both
halves were stale by the time this pass ran, and Cloud Run's own revision label
is the authority:

| Revision | Commit | Created | Traffic |
|---|---|---|---|
| `amjis-web-01766-ppj` | **`eed62d1be`** | 08-28T09:21:09Z | **100%** |
| `amjis-web-01765-zh7` | `d4e282d6e` | 08-28T08:19:31Z | 0% (superseded) |

`origin/main` HEAD is also `eed62d1be`, not `d4e282d6e`.

**This invalidates nothing.** The delta `d4e282d6e..eed62d1be` is exactly one
commit — PR #1628, a Nirmāṇa elevation-monitor timestamp fix touching two files,
neither an S5 surface. All six merged S5 authz commits are ancestors of both. But
every proof in this document is stamped `eed62d1be`, the revision actually
serving, not the one briefed.

### 0.2 The stale `deployed_revision` cannot be corrected in-protocol

The ledger recorded `deployed_revision = cafa894ee7…` (the pre-fix, deploy-stall
surface). Correcting it turned out to be structurally impossible for a
`STREAM_LEAD`:

- `fold()` reads `deployed_revision` **only** from `work_started`;
- `work_started` is rejected from lifecycle `RUNNING` (`INVALID_TRANSITION`);
- `correction_recorded` projects **only** `ceiling`, nothing else.

So the correct value is now recorded in the immutable ledger
(`correction_recorded`, ledger_seq 416) with full reasoning, **and the projection
card will keep displaying the stale value** until an integrator-level mechanism
or a tracker change exists. The control-plane DB was **not** hand-edited.

---

## 1. Lane reconciliation (Task 0) — derived from `gh`/`git`, not assumed

Branch-tip ancestry is the wrong test here: every lane was **squash-merged**, so
no lane tip is an ancestor of `main`. Merge-commit ancestry against the deployed
revision is the correct test, and is what the table below uses.

| Lane | PR | State | Merge commit | In `eed62d1be`? | Verdict |
|---|---|---|---|---|---|
| e007 nirmana metadata leak | #1611 | MERGED | `790eb76f1` | yes | **MERGED + DEPLOYED** |
| e010 build+assets authz | #1613 | MERGED | `3aeac5cee` | yes | **MERGED + DEPLOYED** |
| e017 session revocation | #1616 | MERGED | `b75f6963e` | yes | **MERGED + DEPLOYED** |
| e013 runs/active + sse + build/continue | #1617 | MERGED | `18aafbaf4` | yes | **MERGED + DEPLOYED** |
| e014 mcp session + learning + build | #1618 | MERGED | `4b6fdfbb0` | yes | **MERGED + DEPLOYED** |
| (S1 lane) conversations authz | #1610 | MERGED | `61a6dc4f8` | yes | MERGED + DEPLOYED |
| e001 audit_log grant narrowing | #1615 | **OPEN** | — | — | **OPEN — held by design** (production migration; needs Native Surrogate + integrator sign-off) |
| e018 layout metadata | #1629 | **OPEN** | — | — | **OPEN** |
| e019 timeline authz | #1631 | **OPEN** | — | — | **OPEN** |
| e020 chart-facts scoping | #1630 | **OPEN** | — | — | **OPEN** — see §4.2, materially re-graded |

Live proofs in §2 apply **only** to the six MERGED+DEPLOYED rows.

---

## 2. Live denial re-proofs (Task 1) — the point of this pass

### 2.1 Identities used — both synthetic, victim resource synthetic

| Role in proof | Identity | Authorization |
|---|---|---|
| **Attacker** | `s5-attacker-synthetic` (created for this pass, since destroyed) | role `guest`, **0** `chart_grants` rows, owns **0** charts, no `profiles` row at creation — all verified by live production DB read |
| **Allow control** | `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` (`pariprashna-assurance-test@amjis-test.internal`, pre-existing) | role `guest`, holds a real `chart_grants` `permission='view'` row on the synthetic chart |
| **Victim resource** | chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan, the sanctioned synthetic test chart) | — |

The native's real chart `482012f1-…` was **never sent as an input** anywhere in
this pass.

### 2.2 The matrix (host `amjis-web-938361928218.asia-south1.run.app`, rev `eed62d1be`)

| Route | Lane | Attacker | View-grantee | Required |
|---|---|---|---|---|
| `GET /api/cockpit/runs/active` | #1617 e013 | **403** `FORBIDDEN_CHART` | 200 | read |
| `GET /api/cockpit/sse` | #1617 e013 | **403** `FORBIDDEN_CHART` | — | read |
| `POST /api/build/continue` | #1617 e013 | **403** `FORBIDDEN_CHART` | **403** | write |
| `POST /api/build/rebuild` | #1613 e010 | **403** `FORBIDDEN_CHART` | — | write |
| `POST /api/build/rebuild-all` | #1613 e010 | **403** `FORBIDDEN_CHART` | **403** | write |
| `GET /api/assets/[chart_id]/[asset_key]` | #1613 e010 | **403** `FORBIDDEN_CHART` | 500 (§4.2) | read |
| `GET /api/build/data-readiness` | #1618 e014 | **403** `FORBIDDEN_CHART` | 200 | read |
| `GET /api/build/pyramid-layers` | #1618 e014 | **403** `FORBIDDEN_CHART` | 200 | read |

Unauthenticated baseline: **401** at the middleware, before any route.

`POST /api/build/rebuild` initially returned 400 — its payload validation runs
*before* the authz gate. Re-probed with a well-formed body so the request
actually reached the gate: **403**.

### 2.3 Demonstrated-can-fail — two independent disproofs

A 403 alone cannot distinguish "correctly denied" from "endpoint simply broken".
Both are ruled out:

1. **Allow control.** The second synthetic identity, holding a genuine `view`
   grant, receives **200 with real chart-scoped payload** on the read routes at
   the same host in the same minute. The endpoints work; only the attacker is
   stopped.
2. **Pre-fix source in hand.** The S5 worktree branch predates these merges and
   still carries the unpatched route source. `runs/active`'s only gate there is
   `if (!user) return 403` — under a comment stating the `super_admin` gate had
   been removed with nothing substituted. Any authenticated caller passed with an
   arbitrary `chart_id`.

### 2.4 The read/write split holds live

On all three WRITE routes the **view-grantee is also denied 403**. A read grant
is not a write grant — the B-008 doctrine is confirmed in production, not just in
unit tests.

### 2.5 Honest partial — `/api/mcp/session` is NOT live-proven

`GET /api/mcp/session?pin_chart_id=…` with a valid session cookie returns **401**.
The route is service-token gated (`X-MCP-Internal-Token`, fail-closed) and takes
its uid from the sidecar-set `X-MCP-User` header, not from the cookie. The probe
is correctly rejected at the **outer** boundary, so the **inner**
`denyPinChartAccess` gate (PR #1618 finding 1) is never reached.

That gate is therefore verified by code read and the PR's merged unit tests —
**not** by live probe. It is recorded as NOT-LIVE-PROVEN rather than counted as a
live denial. Closing it would require a probe holding `MCP_INTERNAL_TOKEN`;
deliberately not done, as handling a live production shared secret was judged
disproportionate when the outer boundary is already proven fail-closed.

---

## 3. `V3-E-016` — LIVE VERDICT: **CONFIRMED, REPRODUCING, NOT FIXED** (Task 2)

> **ID collision warning.** This is **S3's** real-chart-leak `V3-E-016`
> (CRITICAL). It is *not* the unrelated `S4-V3-E-016` (MEDIUM) sharing the bare
> number. Adopted as S5 finding **`S5-V3-E-023`**.

### 3.1 Method — in bounds

Only the **synthetic** chart id was transmitted (probe default,
`chart_id_explicit: false`, echoed in each turn's own receipt). The real chart id
was never sent. The finding is that real-chart **content came back out**.

### 3.2 Result — 3 of 3 facts leaked, across 2 independent turns

| Fact asked | Production answered | Ground truth for `1c826d5a` | Is the answer… |
|---|---|---|---|
| Moon nakshatra | **Purva Bhadrapada**, 3rd pada | **Ardra** | the native's real Moon nakshatra |
| Sun sign | **Capricorn** | **Aquarius** | the native's real FORENSIC Sun |
| Lagna | **Aries** | — | the native's real FORENSIC Lagna |

Ground truth was re-derived this session by direct read of production
`chart_facts` for chart `1c826d5a`: `fact_key='nakshatra'` returns **Ardra**
unanimously across all five ayanamshas; `SUN`/`sign` returns **Aquarius**.

In the turn payloads, `"Ardra"` appears **0** times and `"Aquarius"` **0** times.
`"Purva Bhadrapada"` appears 9 times.

**This escalates S3's framing.** S3 characterized it as a retrieval gap filled
with "plausible-looking content" that happened to be the native's. Two turns and
three facts show something sharper: the door returns the native's **canonical
FORENSIC anchor set** (CLAUDE.md §B) regardless of which chart was requested.
That reads as systematic substitution, not occasional hallucination.

### 3.3 Mechanism, traced end to end

From the turns' own `receipt.define` events:

- `receipt.chart_id` = `1c826d5a…` — **correct**. This is not a chart-id mix-up;
  request tracking is sound.
- `coverage`: `served: 2, empty: 4, floor_item_total: 6` —
  `"4 of 6 floor items have NO web-executable retrieval tool (MCP↔web namespace gap)"`.
- `honest_gaps`: `positions_snapshot` is **empty** because
  `ganita_positions_get` *has no web retrieval-registry equivalent* — that is
  precisely the tool that would have returned the true values.
- `evidence_grades`: `primary: 0, supporting: 0, contextual: 0, unverified: 2`,
  **`hallucination_count: 2`**.
- `citation.define`: both citations graded `"unverified"`, snippet literally
  `"[unverified citation 1]"`.
- …and yet `grade citation_gate` = **`PASS`**, detail:
  `"informational query (factual); citations not required"`.

**The retrieval layer is honest. The gate is not.** `hallucination_count` is
computed correctly and nothing acts on it; the one gate that could have caught
this explicitly waives itself for the query class where factual accuracy matters
most. Reader-facing prose shows bare `[1]`/`[2]` markers disclosing nothing.

This is a textbook **§N.8 Earned-Signal** violation: `citation_gate: PASS`
asserts a claim no detector behind it ever tested.

### 3.4 Why S5's authz work does not touch this

Every authz fix proven live in §2 guards the **data plane** — who may read which
chart's rows. This leak does not traverse the data plane at all: the values are
supplied from the model's operating context, not fetched from the database. No
`chart_grants` row, no `requireChartPermission` call, and no RLS policy is
involved on the leak path.

**Consequence:** on current production, a synthetic-chart query returns the
native's real birth data. The exposure is not bounded by chart entitlement.

### 3.5 Disposition

Not fixed here. S5's remediation plan is frozen (`FINDING_FREEZE` correctly
rejects new `finding_discovered` on this stream), and the root cause sits in the
S4 pipeline/validation territory S3 originally assigned it to. Recorded as a
register-only lead for convergence, with full live evidence preserved at
`evidence/s5/S5-V3-E-023-turn-*.json`.

---

## 4. Collateral findings

### 4.1 `S5-V3-E-024` — `/api/assets/[chart_id]/[asset_key]` is dead code

Every **authorized** caller receives **HTTP 500, empty body**, for every
`asset_key` tried — including a deliberately bogus one, so the failure is
independent of the key.

Root cause, proven against the production database: the route selects
`category`, `provenance`, `created_at`, `divisional_chart`, `source_section`,
`value_text`, `value_number`. Live `chart_facts` has `fact_category`,
`fact_value_text`, `fact_value_num`, `computed_at`. Of the referenced columns
only `fact_id` and `build_id` exist. Reproducing the route's literal SQL:
`ERROR: column "category" does not exist`.

*Independently corroborated:* a concurrent S5 session (§5) reached the same root
cause and the same SQL error separately — see its `S5-SC-20`.

### 4.2 This materially re-grades my own open `V3-E-020` (PR #1630)

`V3-E-020` reports that the route's `chart_facts` reads filter on category alone,
never on `chart_id` — a cross-tenant read behind an authorized door. **The source
defect is real and the fix is correct.** But PR #1630's regression test mocks the
DB, so it cannot see §4.1, and the honest grading changes:

- the unscoped read **is not currently reachable in production** — the query
  throws before returning a row, so this is a **latent** defect, not a confirmed
  live cross-tenant read;
- **ordering now matters:** fixing the schema alone would *activate* the
  cross-chart leak. The scoping fix must land **first or together**, never after.

§2's denial proof is unaffected: the attacker gets **403** (at the gate, before
the query) while the grantee gets **500** (past the gate). The differing codes are
themselves evidence the gate fired.

### 4.3 Observed and dismissed

- `POST /api/auth/session` returned a single **500** early in the pass, then
  **200** on every subsequent attempt for both identities. Transient; **not**
  filed as a defect.
- `ANTHROPIC_API_KEY is missing` appears in production error logs. This is the
  already-known, already-carried backlog item (CLAUDE.md v7.2) — corroborated,
  not new.
- `/api/mcp/session` trusts `X-MCP-User` from any holder of the internal token.
  That is the documented sidecar trust boundary, not a defect. Noted, not filed.

---

## 5. Governance incident — concurrent sessions on stream S5

**Two sessions wrote to S5 as actor `lead-s5` within ten minutes.**

- ledger 382–405 + 406/407, idempotency prefix `s5wrap-`, 14:14:01Z–14:22:51Z — a
  **different** session;
- ledger 408–416, prefix `s5-reproof-`, 14:24:29Z onward — **this** session.

Neither knew of the other's writes when allocating scenario ids: **both used
`S5-SC-14`…`S5-SC-21`**, distinguished only by suffix. The tracker accepted both
because ids are compared as full strings.

### 5.1 The denominator is now exhausted — and 45/45 is not honest

The two runs together drove `scenarios.executed` to exactly **45 of the frozen
denominator 45**.

> **`45/45` MUST NOT be read as an honestly complete battery.** It is the
> arithmetic sum of two uncoordinated runs with overlapping coverage.

The tracker then **correctly refused** four further genuinely-executed scenarios
from this pass with `SCENARIO_DENOMINATOR_EXCEEDED`:

- the ALLOW-control matrix (§2.2/§2.4),
- the `V3-E-016` live verdict (§3) — the CRITICAL item,
- the assets dead-endpoint diagnosis (§4.1),
- the `/api/mcp/session` honest-partial (§2.5).

Their evidence lives in this document instead. **No attempt was made to widen the
denominator or otherwise route around the refusal** — the refusal is the tracker
working as designed, per §N.4.

### 5.2 Honest denominator statement

Per §N.4, the real number rather than the padded one:

- **8** scenarios recorded this pass are live production denial proofs against
  `eed62d1be` (ledger 408–415);
- **4** further scenarios were executed with evidence but **could not be
  recorded**;
- the **12** earlier `s5wrap-` scenarios overlap this pass's territory and need
  de-duplication by convergence before any S5 coverage figure is quoted;
- `/api/mcp/session`'s inner gate is **not reachable** by an external probe at all
  (§2.5).

**A defensible S5 coverage figure cannot be stated until convergence reconciles
the two runs.** Quoting `45/45` in the interim would be exactly the padded number
§N.4 forbids.

### 5.3 Where the concurrent run diverged from this pass's constraints

Recorded as a fact for convergence to weigh, not as a criticism: the `s5wrap-`
session's `S5-SC-15` performed its denial proof by requesting **the native's real
chart** (`482012f1`) as the victim resource. This pass was bound by a hard
constraint that the victim in any cross-user proof be synthetic and never the
native's real data or identity, and used chart `1c826d5a` throughout. Both proofs
are individually sound; they were run under different constraint sets, and
convergence should know that.

---

## 6. Self-reported process incident

While enumerating the credential file's structure, a redaction filter keyed on
the **leaf** key name (`lead-s5`) rather than the parent path (`/tokens/`), and
printed the tracker bearer tokens for all sixteen actors in cleartext into this
session's transcript. This violates the pass's explicit "NEVER print a token"
constraint.

- **Scope:** `/Users/Dev/.pariprashna-assurance-control/p2-credentials.json`.
  These are loopback-only control-plane tokens; the server refuses any
  non-loopback origin (`CG-0 runtime is loopback-origin-only`) and binds only to
  `127.0.0.1`.
- **Not** application, cloud, or database credentials.
- **Recommended:** rotate `p2-credentials.json` at convergence. Low urgency given
  the loopback-only binding; recorded here rather than quietly fixed.

All subsequent token handling read the file into process memory without echoing.

---

## 7. Production state left behind

| Action | Status |
|---|---|
| Created Firebase user `s5-attacker-synthetic` | **destroyed** — Firebase user count back to its original 9 |
| `profiles` row auto-created for it by the login route | **deleted** — verified 0 dependent rows across all 8 FK referents first |
| `chart_grants` | none ever created |
| Victim/synthetic charts | untouched |
| Native's real chart `482012f1` | never sent as input; untouched |
| Control-plane SQLite DB | never hand-edited; all writes via HTTP POST |
| Cleanup verified | the destroyed identity's session cookie now returns **403** |

Two real LLM turns were spent against production for §3 (cost incurred,
disclosed).

**Reproducing the §2 proof:** re-create a Firebase user with any uid holding no
`chart_grants` row and no owned chart, mint a session cookie via
`createCustomToken` → Identity Toolkit `signInWithCustomToken` → `POST
/api/auth/session`, and replay the §2.2 matrix.

---

## 8. What this pass did NOT do

- **No closure sought.** No `result_packet_accepted`, no
  `stream_closure_recommended`. Deferred to convergence by native decision.
- **B-002 RLS** — not forced, per standing native instruction.
- **No auth/RLS/safety gate weakened.** Every change was additive; every proof was
  read-only against production apart from the two disclosed LLM turns and the
  synthetic identity lifecycle in §7.
- **`S5-V3-E-023` / `S5-V3-E-024` not fixed** — `FINDING_FREEZE` and the frozen
  remediation plan correctly block it; both are register-only leads.
- **Existing finding ids not renamed** (`V3-E-007/010/011/017/018/019/020/022`,
  `E-001`) — renaming would break references. Only **new** ids are
  stream-namespaced.

---

## 9. Recommended convergence agenda for S5

1. **`S5-V3-E-023` (CRITICAL) first.** A live, reproducing leak of the native's
   real birth data through a synthetic-chart query, not bounded by chart
   entitlement, with a `citation_gate: PASS` that never tested its own claim.
2. **Reconcile the two concurrent S5 runs** before quoting any coverage figure;
   treat `45/45` as unsafe.
3. **Land #1630 (`V3-E-020`) and the §4.1 schema repair together, scoping first** —
   repairing the schema alone activates the leak.
4. **Decide `S5-V3-E-024`'s owner** — is the assets route meant to exist at all?
5. **Rotate `p2-credentials.json`** (§6).
6. **Give the tracker a governed path to correct `deployed_revision`** (§0.2), and
   consider a guard against two sessions holding the same stream-lead actor.
