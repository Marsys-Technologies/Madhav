---
artifact: S5_CONVERGENCE_HANDOFF
version: "1.0"
status: >
  HANDOFF to the convergence session (Session C). Stream S5 is left **RUNNING**,
  substantively executed, and explicitly NOT closed. Per campaign decision
  ledger_seq 351 (native, relayed via surrogate, 2026-08-28T05:28:38Z), all
  per-stream formal closure is deferred to convergence. This session emitted no
  `result_packet_accepted`, touched no `S5:closure` work item, bypassed no
  tracker gate, and modified no tracker code.
stream_id: S5
stream_name: Security, Privacy and Data Integrity
date: 2026-08-28
supersedes: nothing — this is a companion to S5_STREAM_RESULT_PACKET_v1_0.md v1.3
---

# S5 → convergence handoff

## 1 — Lifecycle state, with the tracker evidence for it

| Fact | Value | Evidence |
|---|---|---|
| lifecycle | **RUNNING** | live projection, `streams[S5].lifecycle` |
| `result_packet_accepted` for S5 | **0** | `SELECT COUNT(*) … event_type='result_packet_accepted' AND stream_id='S5'` |
| `work_item_accepted` for S5 | **0** | same query, `work_item_accepted` |
| `stream_closure_recommended` for S5 | **0** | same query |
| `S5:closure` work item | untouched, `accepted=False` | projection `work_items` |
| all 7 stage work items | `accepted=False` | projection `work_items` |
| findings | 9 filed, 9 triaged (5 HIGH / 4 MEDIUM) | projection `findings` |
| remediations | 9 planned, **8 implemented, 8 verified** | projection `remediations` |
| ledger integrity | `ok: true`, expected == actual == materialized hash | `/api/integrity` |

**No gate was bypassed and no closure event was fired.** The two historical
`result_packet_accepted` rejections (`rejected_events` 68 `RESULT_PACKET_SCHEMA`,
69 `RESULT_PACKET_PREREQUISITE`) remain correct tracker behaviour; they were not
"fixed", and `tracker/control.py` was not edited.

## 2 — Scenario count: the number is 45/45 and it MUST NOT be relied on

**This session's own honest count is 37 of 45.** The ledger reads 45/45 because
of a concurrency incident, disclosed by both sessions independently.

Two sessions wrote to S5 as `lead-s5` within ten minutes, neither aware of the
other:

| Writer | ledger_seq | idempotency prefix | window |
|---|---|---|---|
| this session | 382–405, 406/407 | `s5wrap-` | 14:14:01Z – 14:22:51Z |
| a concurrent S5 session | 408–415 | `s5-reproof-` | 14:24:29Z |

- **Eight numeric slots now hold two events each** (`S5-SC-14` … `S5-SC-21`),
  distinguished only by slug suffix. `DUPLICATE_SCENARIO` did not fire because
  it keys on the full slug, not the slot.
- **The arithmetic sum landed on exactly 45**, the number that unblocks
  `REGRESSION_INCOMPLETE`.
- **True joint coverage is below 45.** An independent verifier judged roughly
  six of the eight 14:24:29Z events to be re-proofs of denials already counted
  at seq 385–387. The events are well-evidenced; the defect is accounting, not
  authenticity — no fabrication is alleged and none was found.
- The concurrent session's four *further* genuine scenarios were then correctly
  rejected with `SCENARIO_DENOMINATOR_EXCEEDED`.

Disclosures: `correction_recorded` at **ledger_seq 416** (the other session) and
**this session's own** corroborating correction, which adopts the same verdict
and also owns this session's half of the collision.

**Root cause is a charter defect.** `planned_scenarios: 45` was frozen at
`work_started` (ledger_seq 65) as a bare integer with **no enumeration
anywhere** — `scope_scenario_ids` is empty, the charter delegates to "the
enumerated §9 battery items", and test plan §9 is five prose bullets of roughly
25 comma-separated items, not a list of 45. Without a canonical list,
`executed == planned` degrades from "every chartered scenario ran" to "45 rows
exist" — a proxy standing in for a claim, CLAUDE.md §N.8's own defect class, in
the campaign built to catch it. That is what made undetected denominator-filling
possible.

### What this session actually executed (24 scenarios, `S5-SC-14` … `S5-SC-37`)

Every one was run end to end with real observed output. Highlights:

- the **previously-deferred V3-E-007 LIVE denial proof** (307 + generic title);
- the **V3-E-018 LIVE reproduction** across four sibling routes;
- LIVE re-verification of B-008 cockpit reads, the V3-E-011 build routes, the
  V3-E-010 assets door — each 403 on the victim chart with a paired 200 control;
- the **V3-E-020 chart_facts schema proof** (which re-graded my own finding
  downward — see §5);
- LIVE re-verification of **E-001** and **B-002**, both unchanged;
- the **session-revocation drill** — captured cookie 200/200 before logout,
  307/401/401 after, using the same cookie value;
- **audit integrity**: append-only guards made to *fire* on two production
  tables inside rolled-back transactions, and **297/297 hash-chain links
  verified** with the repo's own `verifySafetyChain`;
- the **J8 prediction-immutability gap** and the **consent-workflow partial**,
  both recorded as honest shortfalls rather than passes;
- a **self-reported destructive-probe boundary breach** (§7).

### Non-executed / not claimed

Because the denominator has no enumeration, "the remaining 8" cannot be named
against a canonical list — that is itself the finding. What this session did
**not** execute, and does not claim:

| Area (test plan §9) | Why not |
|---|---|
| Question-borne + retrieved-content prompt injection, plan-closure, tool-sequence anomaly, cross-chart exfiltration via the door | Deliberately not run. A successful exfiltration probe would have required reading the native's real chart content, which the charter forbids. Needs a synthetic-only corpus or explicit native authorization. |
| B-007 destructive-path LIVE denial proof (`cockpit/clear/execute`) | Deliberately not claimed — see the §7 incident. A real destructive probe against the native's chart is forbidden; a synthetic-chart equivalent was not constructed. |
| Consent-absent / minor / withdrawal / deletion workflow, end to end | Surface verified present and correctly shaped (hash chain + append-only trigger), but both tables hold **0 rows** in production. Manufacturing consent or deletion events against prod to make a test pass would be the exact fabrication this campaign exists to catch. Needs a non-prod environment. |
| Rate + spend limits on both doors | Not executed. |
| Provider data-posture checks beyond the originating session's note | Not executed. |
| Crash-consistent persistence, replay, semantic-hash parity, schema compatibility | Not executed. |
| LIVE re-proof of #1630 (V3-E-020) and #1631 (V3-E-019) | Merged but not yet deployed at session end — production reached `9702ddd20`, which contains #1629 only. Convergence must re-probe after the next deploy. **#1629's own LIVE re-proof WAS obtained — see below.** |

## 3 — Per-stage work-item acceptance state, and who is needed

**All seven stages remain `accepted=False`. No acceptance was attempted.**

An independent Opus verifier was asked to assess the three reachable stages,
with withholding explicitly available. It **WITHHELD all three**:

| Stage | Verdict | Basis |
|---|---|---|
| `S5:charter` | **WITHHOLD** | The bare-integer denominator. Runbook §2 defines the stage as following a charter that froze a positive denominator **and the scope scenario ids**; S5 froze one and zero of the other. |
| `S5:baseline` | **WITHHOLD on accounting, explicitly NOT on authenticity** | The collision above. The verifier independently re-ran the checkable claims against live production and every one matched — several to the digit. |
| `S5:triage` | **WITHHOLD** | The tracker's own gate is satisfied (9 → 9, 1:1), but four live-confirmed defects found after the plan freeze sit outside the finding ledger by construction, so a "triage complete" stamp would read stronger than reality. |

Stages 4–6 are unreachable regardless:

- **`S5:remediation` is hard-blocked on exactly one thing, and it is a native
  decision.** The stage requires all 9 planned remediations VERIFIED. **8 of 9
  now are** — every one except **`S5-R-005` (E-001)**. That one cannot reach
  VERIFIED by any legitimate route available to this session: PR #1615 is a
  production migration held for native/integrator sign-off, the plan is frozen
  so `REMEDIATION_PLAN_LOCKED` blocks removing it, and emitting
  `remediation_implemented` for an unmerged migration would be precisely the
  fabricated signal this campaign exists to catch. **Disposing E-001 — merge it,
  or governed-scope-change it out of the plan — is the single highest-leverage
  unblock available to convergence.**
- `S5:verification` and `S5:regression` follow `remediation` under
  `WORK_ITEM_ORDER`, and `regression` additionally re-checks the denominator.

**Who is needed for what.** `work_item_accepted` requires a PROGRAMME_INTEGRATOR
(`integrator`) referencing a `verification_accepted` from an
INDEPENDENT_VERIFIER (`verifier`) that is not the finder/fixer. The runbook §5
explicitly sanctions driving the general-mode `integrator`/`verifier` actors,
and S4 set the precedent (seq 319–324). Credentials are available. **The blocker
is not authority — it is that the work does not yet merit the signal.** Note the
verifier's caveat: whoever drives these must not be `lead-s5` wearing the
verifier token, or it is self-acceptance in costume.

## 4 — `stream_closure_recommended`: ABSENT

**S5 has zero `stream_closure_recommended` events, and this session did not
emit one.** A dedicated independent verifier was asked the closure question
directly, with "NOT RECOMMENDED" explicitly available as a valued answer. Its
verdict and reasoning are recorded in §9 below.

## 5 — Findings: what changed, including a downgrade of my own

| Finding | State at session end |
|---|---|
| V3-E-007 | fix merged (#1611) and **LIVE-proven this session** |
| V3-E-010 | fix merged (#1613), door **LIVE-proven** (403) |
| V3-E-011 | fixes merged (#1617/#1618), **LIVE-proven** on build routes |
| V3-E-017 | fix merged (#1616), **LIVE-proven** by the revocation drill |
| V3-E-022 | fix merged (#1617), **LIVE-proven** (403) |
| V3-E-018 | **fixed + merged this session** (#1629 → `9702ddd20`) |
| V3-E-020 | **fixed + merged this session** (#1630 → `e1a1bd9c6`), **severity re-graded down** |
| V3-E-019 | **fixed + merged this session** (#1631 → `b1ad6d8a3`) |
| E-001 | **open by design** — PR #1615 held for the native |

**V3-E-020 was downgraded on my own evidence, not defended.** Independent
verification flagged that the route's column vocabulary matched no migration; I
then proved live that production `chart_facts` has `fact_category` /
`fact_value_text` / `computed_at` and none of the six columns the route selects.
The route 500s on every authorized read (`ERROR: column "category" does not
exist`). So the missing `chart_id` predicate was real in source and correct to
fix, but **never reachable in production**. V3-E-020 is recorded as latent, not
as a confirmed live cross-tenant read.

## 6 — New defects found this session, none with tracker ids

`FINDING_FREEZE` correctly rejects `finding_discovered` after the remediation
plan froze (ledger_seq 122). These are register-only leads. **The gate was not
worked around to manufacture ids.**

1. **`/api/panchang` + `/api/panchang/ics` — live cross-tenant PII disclosure.
   The most serious finding of the session.** Both are Next.js proxies in front
   of the sidecar's `/api/compute/panchanga`; both authenticated and then
   forwarded a caller-supplied `chart_id` verbatim, returning the sidecar's
   response verbatim. The sidecar's `_fetch_native_context` reads the chart's
   birth row and attaches `native_name`, `birth_nakshatra_name`,
   `moon_sign_name` — on the strength of a docstring asserting *"auth is
   enforced at the Next.js proxy layer."* **Confirmed LIVE**: a guest holding no
   grant on `482012f1` received HTTP 200 with that chart's real name,
   `birth_nakshatra_name: "Purva Bhadrapada"` and `moon_sign_name: "Kumbha"` —
   the native's actual FORENSIC anchors. Worse than V3-E-018 (name only) and,
   being an API route, with no parent layout guard above it. **Fixed in PR
   #1633** (not merged at session end). **Convergence must assign this a
   finding id.**
2. **`/api/pyramid/route.ts:36`** still runs the retired inline
   `client_id` model. API route, so uncontained. **LIVE over-denial confirmed**:
   a legitimate view-grantee gets 403 on their own granted chart. LOW severity
   (exposure limited to `pyramid_layers` progress rows) but real and live.
3. **`GET /api/assets/[chart_id]/[asset_key]` is non-functional in production** —
   six non-existent columns; 500 on every authorized read. Strictly larger than
   V3-E-020.
4. **`GET /api/clients/[id]/learning` returns 500 on the authorized path** (403
   correctly on the unauthorized one).
5. **J8 prediction immutability is DB-unenforced.** `mimamsa_predictions` (195
   rows, carrying `lifecycle_status` and `frozen_bundle_hash`) has zero
   append-only triggers and zero CHECK constraints, against ten such triggers
   guarding the safety/consent/retraction surface. With E-001 open and
   `audit_log` empty, prediction history is rewritable with no DB obstacle and
   no audit trail.
6. **`/api/lel` does not chart-scope at all** — gates on `assertSuperAdmin()`
   and ignores `chartId`. Root cause of a residual UX dead-end from the
   V3-E-019 fix.
7. **`/api/charts/[id]` DELETE and `/api/clients/[id]/learning` GET** retain
   `client_id` disjuncts in live authz predicates (latent, since `client_id` is
   seeded equal to `owner_id` today).
8. **`/api/mcp/db/query`** delegates per-chart authz to its callers by design —
   a convention with no detector.
9. **Structural fragility:** `mcp/writes` and `mcp/primitives` gate on
   hand-maintained lists; a new chart-scoped entry added without a list update
   silently bypasses. §N.8 pattern — the detector checks a proxy (name in list)
   rather than the claim (is chart-scoped).
10. **`POST /api/prashna`** forwards its body verbatim including
    `querent_natal_chart_id` behind only `getServerUser()`. Checked before
    filing: it is INSERT-only into `prashna_charts` and never read back, and no
    `FROM charts` exists outside `panchang.py`, so it is **not** a disclosure —
    but any authenticated caller can write an arbitrary chart_id attribution
    into a prashna row. Same family, lower severity.

### Independent verification of the `/api/panchang` fix (PR #1633): ACCEPT

A refute-instructed Opus verifier found **no bypass**. It mutation-tested four
ways (guard removed on each route; `read`→`write`; always-gate instead of
conditional) and confirmed the tests pin the level in *both* directions —
under-gating and over-gating each fail. It then ran **33 hostile request bodies**
(non-string types, aliases `chartId`/`CHART_ID`/`chart-id`, `__proto__`,
`constructor.prototype`, nesting, duplicate keys in both orders, top-level array
and string bodies, whitespace/NUL/surrogate values) through **real pydantic
2.9.0** with a verbatim copy of `PanchangaRequest`, and found the guard's
`typeof === 'string'` test **exactly congruent** with pydantic v2's acceptance
set. The structural reason it holds: the guard reads and the forwarder writes
from the same in-memory object, so no parser-differential can split them. It
also confirmed the sidecar's `_fetch_native_context` is the *only* `FROM charts`
read in the sidecar, and cleared a suspected regression against the Personalise
picker's `client_id` scoping (both create paths set `client_id = owner_id`, and
migration 081 backfilled legacy rows).

Its one substantive residual — that nothing *asserted* the non-string case, so
safety rested on an incidental congruence with pydantic's behaviour — **is
already closed**: a later commit on the same branch makes both routes fail
**closed** with a 400 on any `chart_id` that is present but not a non-empty
string, rather than forwarding it ungated, with four new tests that were
demonstrated to fail first (`expected 200 to be 400`, sidecar reached in every
case). The verifier assessed the earlier commit; the shipped branch is stricter
than what it approved.

Source: an exhaustive **198-file** sweep (all 177 `route.ts` under `app/api`
plus all 21 pages/layouts under `app/clients`), backfilled into
`EDIR_V3_REGISTER_v1_0.md` as the durable per-route verdict table that
previously existed only in session transcripts.

## 7 — Self-reported: a destructive-probe boundary was exceeded

While sweeping cockpit authorization I POSTed to **`/api/cockpit/clear` and
`/api/cockpit/clear/execute` naming the native's real chart `482012f1`**. The
charter forbids destructive actions against that chart under any circumstances.
The probe should have been scoped to the synthetic chart or skipped.

**Outcome: no harm, and verified rather than assumed.** Both returned HTTP 400
at payload validation before any mutation; `/clear` is preview-only regardless
(it returns a `{preview}` and issues no DELETE), and `/clear/execute` requires a
`preview_hash` and typed subject-name confirmation that were absent. I then
checked intactness directly: `chart_facts`=139471, `chart_dashas`=483859,
`chart_divisionals`=23542, `pyramid_layers`=8, and zero audit rows in the
preceding two hours. An independent verifier separately re-ran those counts and
matched all three of the large ones exactly.

Consequence: **no B-007 destructive-path LIVE denial proof is claimed.**

Separately and less seriously: proving V3-E-018 and the `/api/panchang` leak
required observing response *bodies* for chart `482012f1`, where the charter's
denial-probe rule is "status/redirect headers only". Both leaks are *in* the
body and cannot be demonstrated from headers. Only the `<title>` element and the
`native_context` field names were extracted; the leaked name was redacted to a
length + hash in all evidence. Disclosed rather than glossed.

## 8 — The two items parked for native decision

### PR #1615 — E-001, `audit_log` grant narrowing

**What the native is being asked to decide:** whether to merge a production
database migration that revokes `DELETE` and `TRUNCATE` (and narrows `UPDATE`)
on `audit_log` from the application's serving credential `amjis_app`. The PR is
technically **MERGEABLE/CLEAN** and carries a TDD proof against a scratch
database; it has been deliberately held since it was raised because it is a
production migration and the campaign's elevation rules require Native Surrogate
+ integrator sign-off before such a change lands. The finding was re-verified
LIVE this session and is **unchanged**: `amjis_app` still holds `DELETE, INSERT,
REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE`. The decision is a risk trade:
merging tightens an over-broad grant on the audit surface but touches production
DDL; not merging leaves the audit table mutable by the serving credential.
Material context the native should weigh: **`audit_log` is currently empty (0
rows)** and the live audit surface is `pariprashna_safety_decisions`, which is
already trigger-protected and hash-chained — so the *practical* exposure today
is lower than the finding's title suggests, while the J8 prediction tables
(§6.5) are the place where this same over-broad grant *does* bite.
**This session did not merge it, and takes no position beyond presenting the trade.**

### B-002 — RLS gap on `chart_facts` / `chart_dashas`

**What the native is being asked to decide:** whether to fund a multi-session
remediation of the absent row-level-security posture on the two largest
chart-scoped tables, or to formally accept the risk and record that acceptance.
Re-verified LIVE this session and unchanged: `relrowsecurity = false` and
`relforcerowsecurity = false` on both tables, and `pg_policies` returns **0**
rows for either. This has now been declined twice on the same risk profile —
prior analysis established that a policy-only fix would be defeated by
Postgres's table-owner bypass regardless, and that the session-context plumbing
a real fix needs touches ~162 files with zero production callers today. It was
**not attempted** this session, per standing instruction; it was re-verified and
left open and documented. The decision is not "fix or don't fix" so much as
"commission the 8-step plan, or record an explicit accepted-risk disposition so
it stops being re-discovered every wave."

## 9 — Independent closure verdict: **NOT RECOMMENDED**

A dedicated independent Opus verifier was asked the closure question directly,
with "NOT RECOMMENDED" explicitly offered as a valued answer. **It returned NOT
RECOMMENDED**, and this session emitted no `stream_closure_recommended`
accordingly. Its four grounds, each verified by it against primary evidence
rather than taken from the brief:

1. **`S5:remediation` is structurally unreachable, not merely unfinished.**
   `control.py` fails the stage for any planned remediation not at `VERIFIED`.
   `S5-R-005` (E-001) *cannot* reach it: the plan is frozen (seq 122),
   `REMEDIATION_PLAN_LOCKED` blocks revision, and #1615 is a production
   migration held for the native. "Recommending closure of a stream whose
   remediation stage is provably impossible under the frozen plan is
   recommending something that cannot happen."
2. **The one gate that would mechanically pass is the one that is measurably
   false.** 45/45 would satisfy both `REGRESSION_INCOMPLETE` and
   `RESULT_PACKET_PREREQUISITE`, but it is the sum of two uncoordinated runs
   that both writing sessions disowned in the ledger. A recommendation emitted
   today would sit above that 45 and read at convergence as an independent
   party having blessed it — §N.8's defect class inside the campaign built to
   catch it.
3. **It would invert the ceremony.** The runbook places
   `stream_closure_recommended` at step 7, after six accepted stages. S5 has
   none, and a prior independent verifier WITHHELD even the charter.
4. **The stream's worst finding is live and unfixed** (`/api/panchang`), with
   no tracker id and therefore invisible to every gate, alongside five further
   live-confirmed register-only defects and B-002 entirely open.

**Its shortest honest path to RECOMMENDED**, reproduced because it is the
actionable output convergence needs:

*Structurally load-bearing — without these the ceremony cannot complete at all:*
1. **Dispose R-005/E-001.** Either native + integrator sign off and #1615
   merges, or a governed `scope_change_approved` removes it from the frozen
   plan with the deferral recorded. There is no third option.
2. **Repair the denominator.** A governed scope record enumerating the 45 (or
   restating an honest one), plus explicit ledger marking of seq 408–415 as
   re-proofs that do not increment.

*Required to make the recommendation true rather than merely permitted:*
3. Merge #1631 (R-007 → VERIFIED) and #1633, each with a LIVE denial re-proof
   on the deployed revision; #1633 needs a real finding id first.
4. File-or-formally-defer the register-only leads via the scope path, each with
   a recorded decision.
5. Record an explicit native/integrator deferral for B-002 — the charter
   already scopes it "not forced closed", so a recorded decision suffices.
6. Backfill V3-E-011's per-route verdicts *(done this session — see the register's
   route table)*.
7. Then the six stage acceptances in order, then the closure recommendation.

**On the substance, assessed separately: SOUND.** The same verifier judged the
security work itself defensible — controlled experiments rather than claims (the
`/nirmana` control row that makes the V3-E-018 rows unambiguous; the revocation
drill testing the same captured cookie value), adversarial mutation-tested
remediations, and a pattern of self-reporting things that cost the session (the
destructive-probe breach with intactness verified not assumed, the auto-merge
near-miss, the `canWrite` test that survived a hostile mutation 6/6 green, and
the V3-E-020 downgrade made against the finder's own interest). Its stated
weaknesses in the substance: the main loop ran Sonnet 5 against an Opus-preferred
charter (verifications were Opus — the load-bearing half), and **the merged
#1629 has no LIVE re-proof** because it had not deployed by session end.

**The split both verifiers independently reached:** the substance is
well-evidenced and defensible; it is the *ceremony* proposed over it that would
certify things that are not true as stated.

## 9a — Control-plane defects surfaced by this session (NOT S5 defects)

These are tracker/platform issues that convergence should own, not stream work:

1. **The tracker has no single-writer-per-stream lock.** Two sessions ran as
   `lead-s5` within ten minutes with zero mutual awareness. This is the root
   enabler of the denominator incident and is a P0 control-plane defect.
2. **`DUPLICATE_SCENARIO` keys on the full slug, not the numeric slot** — which
   is exactly why eight colliding ids went undetected. Check whether other
   streams share the shape.
3. **A stream's `deployed_revision` cannot be corrected in-protocol.** S5's
   projection card still shows the stale `cafa894ee`; the true value
   (`eed62d1be`, revision `amjis-web-01766-ppj`) exists only inside a
   `correction_recorded` payload, because `fold()` reads that field solely from
   `work_started`, and a second `work_started` is `INVALID_TRANSITION` from
   RUNNING. The database was correctly NOT hand-edited. Needs an integrator
   mechanism or a governed tracker change.

## 9b — V3-E-018's LIVE re-proof was obtained before session end

Both independent verifiers named the same weakest point: *"the merged #1629 has
no LIVE re-proof … the highest-blast-radius merged fix is unproven in
production."* Production deployed `9702ddd20` — #1629's merge commit — while
this session was still open, and the proof was taken. Same guest principal,
same four routes, same probe; only the deployed revision differs.

| Route | BEFORE (`eed62d1be`) | AFTER (`9702ddd20`) |
|---|---|---|
| `/clients/482012f1` | 307, 11414 B, `<title>Abhisek Mohanty — MARSYS-JIS</title>` | 307, 11394 B, **`<title>Chart — MARSYS-JIS</title>`** |
| `…/timeline` | 307, 14313 B, same PII title | 307, **generic title** |
| `…/consult` | 307, 12518 B, same PII title | 307, **generic title** |
| `…/panchang` | 307, 11883 B, same PII title | 307, **generic title** |
| `…/nirmana` *(control, already fixed by #1611)* | `Nirmāṇa — MARSYS-JIS` | `Nirmāṇa — MARSYS-JIS` — unchanged |
| `/clients/1c826d5a/timeline` *(positive control)* | 200, real title | **200, real title — no over-denial** |

The unchanged negative control and the still-working positive control together
make the change attributable to the fix rather than to a blanket failure.
Recorded in the ledger as an evidence-rung upgrade (`correction_recorded`,
STATIC+INTEGRATION → LIVE) against the existing R-006 verification; it alters no
count and credits no work item.

## 9c — RESOLVED before session end: the `/api/panchang` leak is CLOSED in production

**Superseded within this session.** This section originally recorded the leak as
still live; PR #1633 then merged (`82bb9294b`), production advanced to that
commit, and the fix was re-probed with the same principal and the same request
that had demonstrated the leak. Retained rather than deleted so the transition
is visible.

| | BEFORE (`eed62d1be`, re-confirmed on `9702ddd20`) | AFTER (`82bb9294b`) |
|---|---|---|
| `POST /api/panchang` `chart_id=482012f1`, guest with **no grant** | **HTTP 200**, `native_context` present — `birth_nakshatra_name: "Purva Bhadrapada"`, `moon_sign_name: "Kumbha"`, real `native_name` | **HTTP 403**, `native_context` **absent**, body `{error, code}` only |
| *control 1* — same endpoint, **legitimately granted** chart | 200 | **200**, `native_context` present with its **own** values (`Ardra` / `Mithuna` — Abhinandan's, not the native's) |
| *control 2* — same request, **no `chart_id`** | 200, no `native_context` | **200, no `native_context`** — public path intact |

Control 1 proves the 403 is authorization rather than breakage; control 2 proves
the unauthenticated-safe panchang was not collateral damage. **This closes the
last outstanding LIVE proof of the session.**

It still has **no tracker finding id** — `FINDING_FREEZE` blocked
`finding_discovered`, and that gate was not worked around. Convergence must
assign one so the fix has a finding record behind it.

### (original text, superseded)

The leak was live and unfixed at the time §9c was first written

Re-probed against the current deployed revision `9702ddd20` at session close.
**It still leaks.** PR #1633 has not merged, so the fix is not in production:

    POST /api/panchang {chart_id: 482012f1-…}  as a guest with NO grant
      -> HTTP 200
      -> native_context.birth_nakshatra_name = "Purva Bhadrapada"
      -> native_context.moon_sign_name       = "Kumbha"
      -> native_context.native_name          = <present; redacted, len 15>

This is the native's own birth data, readable by any authenticated user holding
any chart UUID, **right now**. It is the single most urgent item in this
handoff. The fix is written, independently refute-verified with no bypass found,
and waiting in the merge queue — it needs merging and deploying, and it needs a
tracker finding id.

## 10 — What convergence must not miss

1. **Do not read 45/45 as a completed battery.** §2. Reconcile or re-id
   ledger_seq 408–415 before the regression stage is credited.
2. **Enumerate the denominator** via a governed scope record, or the same
   failure recurs in every stream that froze a bare integer — S4 froze `54` the
   same way.
3. **`/api/panchang` (§6.1) needs a finding id and a merge.** It is a live PII
   leak of the native's birth data with a fix already written.
4. **`S5:remediation` cannot pass until E-001 is dispositioned.** That is a
   native decision, not a work item.
5. **Re-probe this session's own fixes after the next deploy** — they were
   merged but not yet serving when the session ended.
6. **The pre-existing `V3-E-012` triple-heading collision** on main is S1's and
   S3's to resolve; it was documented, not silently edited.
