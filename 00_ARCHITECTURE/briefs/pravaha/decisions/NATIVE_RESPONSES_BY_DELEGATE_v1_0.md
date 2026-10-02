---
artifact: NATIVE_RESPONSES_BY_DELEGATE
version: "1.0"
status: "RESPONDED (delegated) — the four items left waiting on the native after NATIVE_RULINGS_BY_DELEGATE v1.0 (the nine credential/infrastructure acts of its §3.6; the seal-approver confirmation; ND-DASHA-PLURALITY-TIERS; the BPHS graduated-aspect human re-read) are answered here, plus a check of every other item in NATIVE_OPEN_DECISIONS v1.10. The native may overrule any response by a later, dated ruling; nothing here is edited afterwards — a change is a new version."
date: 2026-10-02
author: "Fable 5.1 (Claude), a delegated agent responding for the native (Abhisek Mohanty, chart 482012f1-710e-4a25-994a-93821f5871aa) at his instruction, given in the campaign steward's window on 2026-10-02, that one agent answer every item still waiting on him. I decided and wrote; I changed no code, applied nothing, created no role, account or secret, ran no production write or production database query, merged nothing, ran no git write command."
relation_to_rulings: "Companion to decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md (2026-10-02). That file RULED the open decisions and stated conditions; this file answers what that file deliberately left to the native: it gives the go-ahead (with conditions) for the §3.6 acts, confirms the seal approver, decides the daśā plurality question, and dispositions the BPHS re-read. Where the two files touch, this one narrows, never widens."
basis_of_authority: "PRAVAHA_EXECUTION_ARCHITECTURE v1.0 §5a (native, 2026-09-30) reserves D-FLIP, D-T2, production chart-data writes and credential changes to the native and lets the steward delegate everything else. The credential acts answered in §2 are therefore NOT covered by that standing delegation; they are covered only by the native's specific instruction of 2026-10-02 (relayed in the steward's window) that a single agent respond on his behalf to all waiting items. That instruction reached me through the steward, not in the native's own written words. Two consequences are built in below: every act is reported back to him as it is done, and a 'stop' from him halts the sequence at the next act boundary."
reserved_to_native_personally: "D-FLIP; D-T2; the dispatch of the protected migration window (act 9); holding the seal-approver identity and performing every generation-seal approval himself (no delegate, human or agent, ever); the one-time live-gate proof approval; the human read of BPHS lines 16496–16502 (a formality, due before D-FLIP); ND-NODE-VEDHA at its deadline if no source is found."
response_id_grammar: "NRS-<ITEM>-20261002, matching migration 1206's ruling grammar ^[A-Za-z0-9._-]+$ so the ids can be cited in pins alongside NR-ROLES-20261002 etc."
what_i_verified_myself_this_session: >
  Local BPHS vol.1 file (path, sha256, line count, lines 16490–16510 and 16600–16635 read); the spec and
  oracle citations of BPHS1:16496-16502 (GOCHARA_DESIGN_SPECS_v1_4.md:820, GOCHARA_TEST_ORACLES_v1_4.json:429);
  served-corpus chunks hora_sara:PG20:C1, jataka_parijata:PG99:C1 (via read_chapter), uttara_kalamrita:PG40:C2;
  read_chapter(bphs, 26) returns chapter-1 chunks (defect confirmed); the repository's GitHub deployment
  environments and their protection rules (read-only API); the GitHub and GCP identities the steward's CLIs act
  under (read-only); the composed rehearsal's order of role creation vs. migrations (test_a53_inventory.py);
  PR #2954's metadata and description (read-only); the Stage-1 freeze draft's placeholder; Codex round 10
  (ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_9.md) in full. Production database: NOT queried; the packets' read-only
  figures are taken as reported and said so.
---

# Responses by the native's delegate — the four items waiting on him, 2026-10-02

Citation keys (paths under `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/` unless absolute):
**RUL** = decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md · **IDX** = decisions/NATIVE_OPEN_DECISIONS_v1_0.md (v1.10) ·
**ROLES** = decisions/ND_ROLES_DECISION_PACKET_v1_0.md (v1.2) · **DPT** = decisions/ND_DASHA_PLURALITY_TIERS_v1_0.md ·
**CDX10** = reviews/ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_9.md (Codex round 10, REJECT) · **RR11** = reviews/REVIEW_REQUEST_A5_5_GATE_v1_11.md ·
**FRZ** = measurement/STAGE1_FREEZE_PREP_4_1_v1_0.md (v1.4) · **FRZJ** = measurement/FREEZE_STAGE1_4_1_v1.DRAFT.json ·
**EXA** = PRAVAHA_EXECUTION_ARCHITECTURE_v1_0.md · **CLAUDE** = /Users/Dev/madhav-l3/pravaha/CLAUDE.md. `CDX10:177` means line 177 of that file.

---

## 1. One-screen table

| Item | Response (one line) | What the steward may now do | What still needs the owner in person |
|---|---|---|---|
| **1. Go-ahead for the nine §3.6 acts** (`NRS-CREDENTIAL-ACTS-20261002`) | **Given, conditionally, act by act.** The two roles and their containers are created **once, in the same sitting as — and immediately before — the protected-window dispatch**, so that 1240's role-guarded grants fire (the rehearsed order; removes Codex R10-7's late-role case without a backfill). The verification **job** (act 6) deploys only after Codex accepts the job's code. The steward executes under the owner's CLI identities from a written runbook, reporting each act back before the next. | Merge act 7 now (reviewed); write the runbook; execute acts 3→4→1→5→2 when the named window preconditions hold; act 8 after the window; act 6 after Codex ACCEPT of the job; the live-gate proof (§3.4). | **Act 9** (dispatch); **the seal-approver identity** (§3.3 — today's `amonty84` does not qualify while its token sits on the steward's machine); the **live-gate proof approval**; a "stop" at any act boundary if he wants one. |
| **2. Owner = required approver of every seal** (`NRS-SEAL-APPROVER-20261002`) | **Yes.** He is the **only** required reviewer of `gochara-seal`; **no delegate — human or agent, including the steward and including me — may ever approve a seal in his place**; a second reviewer is not added while the chart is his own. "Approval" means reading the **seal brief** of §3.2 (computed from the database by the seal's own gate function) before clicking. | Build the sealing workflow so the brief is shown before the gate and the gate is re-checked inside the seal; configure the environment per §3.3; never call any approval API. | **Every seal approval**, from a device only he controls. If he is unavailable, publication waits. |
| **3. Daśā plurality for '4.1'** (`NRS-DASHA-PLURALITY-20261002`) | **Option (a) — keep**, defined precisely: the voting set is **frozen by (system, level) name** as what votes today (Vimśottarī L1–L4; Mudda L1; Nārāyaṇa L1), under PR #2954's per-(system, level) policy; the five others `unavailable` with reason; denominator 1.0; ceiling 0.66; every value labelled **partial**. **(b)** is deferred to its own decision for governed `'5.x'` after R-VOCAB-1; **(c)** and **(d)** rejected. **Frozen now, before any '4.1' output exists.** | Fill FRZJ's `dasha_plurality_tier_policy.version` with "(a) + PR #2954 policy @ <commit>" and the observed per-(system, level) tiers; complete the Stage-1 freeze. | Nothing. |
| **4. BPHS graduated-aspect human re-read** (`NRS-BPHS-REREAD-20261002`) | **Not discharged by delegation — and it blocks nothing.** I re-read the local file (hash and lines verified, text quoted in §5) and all three served corroborations; an agent's read is still not a person's read, and a "human confirmation" item cannot be handed to an agent without making its label false. It stays open as a **one-minute formality, due before D-FLIP**, with the exact procedure in §5.4. | Nothing; carry the item with its new deadline. | **Read seven lines once** (procedure §5.4) and write one dated line in the tracker. |
| **Everything else in IDX** | ND-NODE-VEDHA: stands as ruled, **not due now** (deadline unchanged). D-FLIP, D-T2: **not due** (J2). Window dispatch: **not approvable now** (Codex (a) BLOCKED). Nothing else is waiting. | — | — |

Still in force and not mine to lift: **ST-P5-HOLD-20261001**, **ST-H-UNKNOWN-20261002**, and every ruling in RUL.

---

## 2. Item 1 — the nine credential and infrastructure acts (RUL §3.6) — `NRS-CREDENTIAL-ACTS-20261002`

### 2.1 The question, in plain words
Option A (RUL §3) needs two new database "keys" (a verifier login and a sealer login), a place for each password to live, a machine identity for the verification job, and an approval gate for sealing. Nine concrete acts create them. RUL said each needs the owner's explicit go-ahead and left three things open: **when** to do them, **who** does them, and **under what conditions**.

### 2.2 The response
**The go-ahead is given, act by act, under the conditions in §2.5.** Three decisions shape it:

**(a) WHEN — the principals are created once, against the settled names, in the same sitting as the protected-window dispatch, immediately before it.** Not now, and not after the window.
- *Why not after the window (the backfill route):* migration 1240 grants to the verifier and sealer **only if the roles exist when it runs**; skipped grants are not queued (CDX10:177). Roles created afterwards would need "a reviewed additive grant backfill covering both 1240 and 1241" and a new rehearsal of "absent-role → create-role → grant → verify/seal" (CDX10:183). That is a new migration, a new review and a new rehearsal, all to recover grants that fire by themselves if the roles simply exist first.
- *Why "roles first" is safe:* the composed rehearsal already runs that order — its deployment-faithful mirror creates `gochara_verifier` and `gochara_sealer` **before** applying 1206/1232/1240 "so their role-guarded grants apply" (`/Users/Dev/madhav-l3/pravaha-b-rehearsal/platform/python-sidecar/tests/l3/gochara/test_a53_inventory.py:231–242`; 56/56 PostgreSQL tests, RR11:31). Roles-first is the **rehearsed** path; the backfill route is not. A role with no grants holds nothing (ROLES:69: "the verifier/sealer have no privileges until [1241] runs").
- *Why not now:* nothing can use the principals before the window, and the window is itself blocked (CDX10:227: (a) BLOCKED by R10-1, R10-2, R10-3, R10-4, R10-7; 1240 and 1241 both REJECT pending amendment, CDX10:88–89). Creating them now would leave live-capable logins idle for an unknown period against a design whose final bytes are still moving. "Once, against a settled design" (the steward's recommendation) is honoured by tying creation to the dispatch sitting.
- *The one act that may run now:* act 7 (the secret-isolation preflight extension) is a **deploy gate** — merging it early makes the gate stricter, not looser, and it must know the verifier pair before deploy.yml ever references the pair.
- *The one act that waits longest:* act 6 (the verification job's deployment). Deploying a job that can write `VERIFIED` rows while Codex has shown its detectors incomplete (R10-1, R10-3, R10-4, R10-5, R10-6) would manufacture a status with no earned signal behind it — CLAUDE §N.8. Act 6 waits for Codex ACCEPT of the job at source.

**(b) WHO — the steward executes acts 1–5, 7 and 8; the owner executes act 9 and holds the approver identity.** The steward is a Claude session whose `gh` and `gcloud` CLIs act as the owner's own accounts (verified read-only this session: `gh api user` → `amonty84` "Abhisek Mohanty"; `gcloud auth list` → active `mail.abhisek.mohanty@gmail.com`, project `madhav-astrology`). So every act will appear in GitHub's and Google Cloud's audit logs under the owner's identity. That is acceptable **because** he has delegated it and **on condition that** each act's report says so explicitly (identity used, timestamp, audit-log reference). The owner, a non-programmer, is not asked to type any command; he is asked to read each report and to say "stop" if anything reads wrong.

**(c) CONDITIONS — concrete, checkable by a third party, per act (§2.5), plus the general safeguards of §2.4.**

### 2.3 What I am and am not authorising
- **Authorised:** the steward may perform acts 1, 2 (in two parts), 3, 4, 5, 7 and 8 exactly as specified in §2.5, each only once its preconditions are verified true, each followed by its report. Nothing else, and nothing by analogy.
- **Not authorised by this file:** act 9 (the owner's); any approval of any deployment to `gochara-seal` by any agent or token (§3); any `gcloud sql users create` or console-created database user (it would silently make the principal a `cloudsqlsuperuser` member — see act 1); any membership edge, `SET ROLE` path or second credential in the builder's process (option A forbids them; ROLES:31, 43); any automatic trigger of the verification job from the orchestrator or from build completion (RUL §3.2 "Trigger"); any editing of an applied migration (CLAUDE §N.4); any production chart-data write.
- **Reversibility:** every authorised act has a rollback named in §2.5. The two acts with no rollback (the window dispatch; applying 1241) are the owner's or ordinary-deploy acts with their own verification.

### 2.4 General safeguards (apply to every act)
1. **A written runbook before execution.** `runbooks/CREDENTIAL_ACTS_RUNBOOK_v1_0.md` (or the steward's name for it) lists, per act: the exact command(s), the preconditions and the read-only check that proves each, the expected output, the read-only verification after, the rollback, and the report template. The steward executes the runbook **as written**; any deviation, surprise or failed check means **stop, report, do not fix forward**. The runbook is posted to the owner with this file before any act runs.
2. **Passwords are never seen by anyone.** Generated at execution by a cryptographic random generator (e.g. `openssl rand -base64 48`), piped in **one** pipeline into the `ALTER ROLE … PASSWORD` statement over the admin connection and into the secret store (`gcloud secrets versions add … --data-file=-` / `gh secret set --env … --body-file -`); never echoed, never typed interactively (so never in shell history), never written to a file, never pasted into any message, tracker entry or chat. The report carries only the secret's resource name and version id.
3. **Each act is confirmed back before the next begins.** The report (tracker `pravaha report`/decision request to the owner, in his inbox the same day) contains: act number; identity used; UTC timestamp; resource names created; the read-only verification output (no secrets); the rollback command; the audit-log reference. A "stop" from the owner halts at the next boundary.
4. **Least privilege, stated per act** (§2.5). Nothing is granted "for convenience"; 1240/1241 are the only grant sources for the two roles.
5. **Pre-existence is a stop condition.** If a role, service account, secret or environment of the intended name already exists when the runbook checks, the steward stops and reports — it means someone else acted, or an earlier attempt half-ran.
6. **No production database query beyond the named read-only checks**, and none of them touches chart data.
7. **The cockpit line "BUILT · NOT VERIFIED · gate CLOSED (n reasons)"** (RUL §3.3) is required before the first verification run so the first `VERIFIED` has a visible, database-derived predecessor state.

### 2.5 Per act: who, when, conditions, verification, rollback, report

Order of execution: **7** (now) → *[window preconditions hold; dispatch scheduled]* → **3 → 4 → 1 → 5 → 2a** → *[live-gate proof, any time before the first seal]* → **9** (owner) → **8** → *[L1 read ACLs by the data-plane owner]* → *[Codex ACCEPT of the job]* → **2b → 6** → first operator-dispatched verification → first seal (owner approves).

| # | Act | Executor | When / preconditions (all must be TRUE, each by a read-only check) | Least privilege & specifics | Verification after (read-only) | Rollback | Report back |
|---|---|---|---|---|---|---|---|
| **7** | Extend `platform/scripts/data-plane-secret-isolation-preflight.ts` to know the verifier SA/secret pair | Stream B authors; steward reviews and queues | **Now.** Code only. CI green; the change adds the pair `gochara-verifier-runtime@…` / `gochara-verifier-db-url` and changes **nothing** about the builder pair (`BUILDER_SERVICE_ACCOUNT`, `BUILDER_SECRET`, lines 5–6 today) | The gate must assert: builder SA binds only the builder secret; verifier SA binds only the verifier secret; neither can read the other's; unknown pairs still fail | CI run id; the gate's own test output | Revert the PR | PR number, merge commit, CI run id |
| **3** | Create GCP service account `gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com` | Steward (owner's gcloud identity) | All of RUL §4 item 3's window preconditions hold **as amended by §2.6 below**; the owner has fixed the dispatch time; act 7 merged; the SA does not exist | Project roles: the **minimum** the builder SA holds for Cloud SQL connectivity and logging (mirror it, list it in the report), and **no** project-level Secret Manager role; **no key file ever created** (runtime identity only) | `gcloud iam service-accounts describe`; `gcloud projects get-iam-policy` filtered to the SA (roles listed) | `gcloud iam service-accounts delete` | SA email, roles held, audit-log reference |
| **4** | Create Secret Manager secret `gochara-verifier-db-url` (container) and the IAM binding letting **only** #3 read it | Steward | Act 3 done and verified; the secret does not exist | Binding: `roles/secretmanager.secretAccessor` for #3 **on this secret only**; the builder SA must not be able to read it; #3 must not be able to read `data-plane-builder-db-url` | `gcloud secrets get-iam-policy gochara-verifier-db-url` shows exactly one accessor binding; the same command on the builder secret shows #3 absent; act 7's gate passes | Destroy versions; delete secret; remove binding | Secret resource name; policy output |
| **1** | `CREATE ROLE gochara_verifier LOGIN NOINHERIT` in production, password straight into #4 | Steward, over the ownership-admin SQL path (`DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL` / Cloud SQL admin connection) — **a SQL `CREATE ROLE`, never `gcloud sql users create` or the console** (those make the user a member of `cloudsqlsuperuser`) | Acts 3–4 done; `pg_roles` shows the role absent; still inside the dispatch sitting | Attributes: `LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`, a connection limit sized to the job and recorded in the runbook; **no GRANT of any kind**, **no membership edge** (1240/1241 are the only grant sources); the DSN (host/db/user/password/sslmode) written as version 1 of #4 in the same pipeline as the password (§2.4 item 2) | `SELECT rolname, rolcanlogin, rolinherit, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls, rolconnlimit FROM pg_roles WHERE rolname = 'gochara_verifier'`; `SELECT pg_has_role('gochara_verifier','cloudsqlsuperuser','MEMBER')` = **false**; `SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname='gochara_verifier') OR roleid = (…)` = **0**; `SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = 'gochara_verifier'` = **0**; `data-plane-ownership-status.ts` still green (the name is outside `data_plane_`, so the name gate and DP-SD-018 are untouched — ROLES:32, 44) | `DROP ROLE gochara_verifier` (preceded by `DROP OWNED BY` if anything was ever granted); destroy the secret version | The five query outputs; secret version id; audit-log reference |
| **5** | Create the approval-gated GitHub environment `gochara-seal` and its environment secret container | Steward creates the environment; **the owner supplies and holds the approver identity (§3.3)** | Act 1 done; **the approver identity of §3.3 exists and satisfies its condition**; the environment does not exist | In **one** API call: `required_reviewers` = exactly one reviewer = the owner's approver identity; `prevent_self_review: true`; "Allow administrators to bypass configured protection rules" **OFF** (`can_admins_bypass: false` in the API); deployment branch policy = **protected branches only**; the sealer secret is **not** created until the reviewer rule is confirmed present (a secret in an environment without a human gate is a seal path with no gate). Note: the existing `data-plane-production-cutover` environment has **no required reviewers** and `can_admins_bypass: true` (read-only API, this session) — it is **not** the pattern to copy for sealing; `gochara-seal` must be stricter | `gh api repos/Marsys-Technologies/Madhav/environments/gochara-seal` shows the four settings above; the reviewer login is the §3.3 identity; the environment-secret list is empty until act 2b | Delete the environment (its secrets go with it) | The environment JSON (no secrets); reviewer login |
| **2a** | `CREATE ROLE gochara_sealer LOGIN NOINHERIT` in production **with no password** (`PASSWORD NULL` — a role whose password is NULL cannot authenticate by password at all) | Steward, same SQL admin path as act 1 | Act 1 done; `pg_roles` shows the role absent; still inside the dispatch sitting | Same attributes as act 1; **no GRANT, no membership**; the role exists so 1240's role-guarded sealer grants fire, but **cannot log in** until act 2b | Same five queries as act 1 for `gochara_sealer`; additionally `SELECT rolpassword IS NULL FROM pg_authid …` if the admin path can read `pg_authid`, else the runbook records that the `CREATE ROLE` statement carried no `PASSWORD` clause | `DROP ROLE gochara_sealer` | Query outputs; audit-log reference |
| **9** | Dispatch the protected migration window (routine 1234/1236 before; then 1204 → 1206 → 1232 → 1233 → 1240; then routine 1241 — CDX10:96) | **The owner personally** | RUL §4 item 3 **as amended by §2.6**; acts 1, 2a, 3, 4, 5 done and reported (so both roles exist when 1240 runs) | — | The deploy's own ledger output | None (protected migrations refuse re-application; forward-fix only) | — |
| **8** | Apply 1241 by the ordinary deploy after the window; **verify it applied and granted to both principals** | Ordinary deploy; steward verifies | The window completed; 1241's final bytes carry Codex ACCEPT (today REJECT pending R10-7, CDX10:89) | 1241 is grants-only, role-guarded, prints the principals found (ROLES:73) | (i) 1241's post-check line names **both** principals (a line naming zero or one principal = **STOP**: the roles were missing at application — the backfill route is then unavoidable; never edit 1241 after it is applied); (ii) verifier: INSERT (+ pre-seal DELETE) on exactly `ka_gochara_search_inventory_verification` and `ka_gochara_eval_window_verification`, SELECT on the read set, EXECUTE on the guard functions, **nothing** on any builder-written table; (iii) sealer: the seal set only (SELECT on the seven read tables, INSERT on `ka_gochara_generation_seal`, UPDATE on `kala_gochara_publication`, EXECUTE on the seal-side functions), plus whatever Codex's R10-7 "legacy relation" closing change settles for `kala_gochara_windows`; (iv) builder: **no** privilege on either verification table (PC-4); (v) 1240's own role-guarded grants are present (they fired because the roles existed) | A new REVOKE migration (never an edit) | The post-check line verbatim; the ACL query outputs |
| *(not one of the nine)* | SELECT on L1 `chart_facts` and `chart_dashas` for **both** principals, via the data-plane ownership preflight's allowlist (ROLES:72; RR11:35) | Data-plane ACL owner | Before the first verification run; RLS is off on both tables so a table-level SELECT suffices (RR11:35) | SELECT only; neither principal reads `charts` | `has_table_privilege` for both roles on both tables = true | Allowlist revert | Allowlist commit |
| **2b** | Set the sealer's password: `ALTER ROLE gochara_sealer PASSWORD …` piped into `gochara-sealer-db-url` as an **environment secret of `gochara-seal`** in the same pipeline | Steward | Act 5 verified **with its reviewer rule present**; the live-gate proof of §3.4 has passed (so the gate is known to hold before any credential sits behind it) | The DSN lives **only** in the environment secret; no copy in Secret Manager, no copy anywhere else; only jobs declaring `environment: gochara-seal` can read it (GitHub's enforcement) | `gh secret list --env gochara-seal` shows the one secret; `gh api …/environments/gochara-seal` still shows the four protection settings unchanged | `ALTER ROLE gochara_sealer PASSWORD NULL`; delete the environment secret | Secret name; confirmation the four settings are unchanged |
| **6** | Define the Cloud Run job `gochara-verification-job` in `deploy.yml` (same image, verifier entry point, SA #3, secret #4) | Stream A + steward | **Codex ACCEPT at source of the verification job** — R10-1 (complete expected-record derivation), R10-3 (lock before read), R10-4 (mandatory input-identity rederivation, real runner identity recorded, combined gate called), R10-5 (identity check covers column grants and login/session separation), R10-6 (one boundary contract) closed; the composed rehearsal **re-run on the final bytes** (CDX10:223); acts 1, 3, 4, 7, 8 and the L1 ACLs done | The job reads exactly one credential (`GOCHARA_VERIFIER_DB_URL` from #4); runs as #3; is **dispatched by an operator only** (never by the orchestrator, never on build completion); refuses by name and writes nothing on any identity or precondition failure | `gcloud run jobs describe` shows SA #3 and the one secret; act 7's gate passes in the deploy; a first run against the held candidate ends in rows **or** a named refusal, never a silent exit | Revert the PR; `gcloud run jobs delete` | Job name; describe output; first run id and its exit code/reason |

### 2.6 Amendment to the window's preconditions (RUL §4 item 3)
Because §2.2(a) chooses roles-first, the protected window gains one precondition and one restatement:
- **New:** acts 1, 2a, 3, 4 and 5 are done and reported, verified by the read-only queries of §2.5 showing both roles present with `rolcanlogin = true`, `rolinherit = false`, `rolsuper = false`, no `cloudsqlsuperuser` membership, no grants, no membership edges.
- **Restated from Codex round 10 (CDX10:227, 88–89, 223):** R10-1, R10-2, R10-3, R10-4 and R10-7 closed at source; 1240 and 1241 ACCEPT on their **final** bytes; the composed rehearsal re-run on those bytes; 1206's unapplied status re-confirmed read-only immediately before dispatch (CDX10:84); routine 1230/1234/1236 applied by the ordinary deploy first (RR11:57).
RUL §4 item 3's other conditions stand unchanged.

### 2.7 What stays disclosed
Until acts 1–8 and the first verification run are complete: "the first candidate is built and held; it is **not verified** and **cannot be sealed**; the gate is closed by design" (RUL §3.5). Every act report is part of the campaign record.

### 2.8 How this response can be changed later
By the owner's dated ruling at any act boundary ("stop", "wait", or a different executor); by a later Codex round that changes a precondition (which binds automatically through §2.6's restatement); or by a new version of this file. No act already performed is undone by a change of policy — its rollback is a separate, reported act.

---

## 3. Item 2 — is the owner the required approver of every generation seal? — `NRS-SEAL-APPROVER-20261002`

### 3.1 Response
**Yes.** The owner is the **sole** required reviewer of the `gochara-seal` environment, for every seal of every generation, including the first all-NULL `'5.0'` candidate.

**May any delegate approve in his place? No — never.** Not an agent (not the steward's session, not a Fable delegate like me, not a scheduled job), and not a second human while the chart being sealed is his own. Reasons:
- The seal is the publication step — the one point where an agent-built, agent-verified candidate becomes a sealed generation. The verifier job is an agent; the builder is an agent; the reviewers are agents. If the approver is also an agent, nothing human has looked at the thing before it becomes publishable, and the approval is a status with no detector behind it (CLAUDE §N.8).
- A seal is a production chart-data write (INSERT on `ka_gochara_generation_seal`, UPDATE on `kala_gochara_publication`) — a class of act the native kept for himself even under the standing delegation (EXA §5a). My delegation today does not reach it, and I would decline it if it did.
- GitHub's required-reviewer rule is satisfied by **any one** listed reviewer. Adding a second reviewer therefore creates a path around the owner, not a second check. RUL §3.2 Q2's clause "a delegate may be added only by the native" is narrowed: **no second reviewer** for `gochara-seal` while the generation sealed is his own chart's.
- If he is unavailable, the seal waits. Publication is never urgent.

### 3.2 What "approval" must consist of to be meaningful
Clicking "Approve" on a bare GitHub deployment page is not a check. The sealing workflow must show him a **seal brief**, computed in a job that runs **before** the environment-gated job (so it needs no sealer credential) and printed to the run summary, containing — every line from the database by the same functions the seal uses, never from the orchestrator's build state:
1. Chart id and generation; the candidate manifest's id and its status (`candidate`).
2. `ka_gochara_candidate_gate_violations(...)` (the **combined** gate — the same call the seal triggers make; CDX10:153) = **0**, with the violation list if not.
3. Verification: how many of how many (class, path) grains are `VERIFIED`; the verifier policy version; the verification job run id; the **runner's recorded code identity** (commit/digest — R10-4's requirement); the timestamps.
4. The result policy in force (for the first candidate: all numeric result fields NULL; the candidate serves nothing).
5. Migration ledger state: 1240 and 1241 applied (filenames and `applied_at`).
6. The disclosures that will attach to the sealed generation (RUL §2's "what stays disclosed" lines that apply).
7. One sentence on what sealing does and does not do: **a seal is not a flip**; nothing is served until D-FLIP, which is a separate decision of his.
8. The exact `DEPLOY_SHA` of the sealing code and a link to the review verdict that accepted it.

He approves only if the brief reads as he expects. Anything unexpected → **Reject** in GitHub, and the steward investigates. Inside the gated job, the sealing step re-checks the gate (the 1206/1240 seal triggers refuse unless every required verification row exists, is `VERIFIED` and still matches the stored data — ROLES:64), so what he was shown is what is sealed, or the seal is refused. The seal row records the approver login and the run id (RUL §3.5).

### 3.3 The approver identity — a condition with a finding behind it
A human gate is real only if agents cannot operate it. This session found (read-only) that the steward's `gh` CLI acts as **`amonty84` — Abhisek Mohanty**. If `amonty84` were the required reviewer, the steward's own token could approve a seal, and GitHub could not tell the two apart. So:

**Condition:** the required reviewer of `gochara-seal` must be a GitHub identity **for which no credential exists on any machine or in any session an agent can use**. The owner chooses one of two ways to satisfy it — **his act, in person**:
- **(i) a dedicated approval account** of his (used only from his phone or browser, never authenticated in any CLI), added to the repository with the least role that can be a reviewer; or
- **(ii) keep `amonty84` as reviewer and remove its token from every agent-accessible machine**, re-authenticating the steward's `gh` as a different account (or a fine-grained token) that cannot approve deployments — a larger change to the steward's tooling, but his to choose.

**Checkable:** `gh api user` on the steward's machine returns a login **different** from the reviewer login; and the live-gate proof below shows an approval attempt under the machine token is **refused**.

**Policy rule regardless of mechanism:** no agent ever calls any deployment-approval API or UI for `gochara-seal`, with any token, for any reason. A seal whose approval record is not by the §3.3 identity from the owner's own device is treated as **unapproved**: the generation is not flip-eligible and the seal is reported as an incident.

### 3.4 Live-gate proof (one time, before the first seal; after act 5, before act 2b)
A no-op workflow run that only prints a line is dispatched to `gochara-seal` by the steward. It must (1) **wait** for approval; (2) the steward attempts approval through `gh api` under the machine token and the attempt is **refused** — this proves the machine identity cannot approve; (3) the owner approves from his own device; (4) the job runs. The report carries the run id, the refused attempt's output and the approval record (login, timestamp). Only after this does the environment count as live, and only then is the sealer's credential placed behind it (act 2b).

### 3.5 How this response can be changed later
Only by the owner's dated ruling, and only in one direction that keeps the check real: he may name a different **human** approver identity of his own. He cannot, by a ruling, make an agent an approver — that would be a change to the architecture's human gate (CLAUDE §L: no architecture change without native approval **and** a version bump — and I record here that I would advise against it).

---

## 4. Item 3 — which daśā systems vote in the '4.x' permission — `NRS-DASHA-PLURALITY-20261002`

### 4.1 The question, in plain words
The old ('4.x') engine lets twelve timing systems vote on how "open" a time is. Eight are daśā systems; five of those are stored at a checking level the engine refuses to read, so **34 % of the vote can never be cast** and the permission can never exceed **0.66**. Nothing told the reader. Before the '4.1' diagnostic measurement is frozen, one policy must be chosen (DR-15(d): no post-hoc adjustment), because the permission arithmetic enters the stored '4.1' intensities (DPT §"Interaction"; FRZJ:188–192).

### 4.2 The response — option (a), keep, defined precisely
**The voting set is frozen by (system, level) name as what votes today:** Vimśottarī levels 1–4 (strict two-pass verified), Mudda level 1, Nārāyaṇa level 1 — under **PR #2954's per-(system, level) accepted-set policy** (`pravaha/a58-honest-tier-readers`, OPEN; read-only this session), which is strict everywhere except that Mudda/L1 and Nārāyaṇa/L1 accept their honest computed tier. The other five systems (Chara, Yoginī, Aṣṭottarī, Naisargika, Kālacakra) are **`unavailable` with a stated reason** — never `inactive` (PR #2954's "UNAVAILABLE ≠ inactive"). The denominator stays **1.0**; the ceiling stays **0.66**; every '4.1' permission value is labelled **partial**, with the unavailable systems named. **No stored number changes.**

**One clarification I add, because it is where (a) could silently break:** PR #2954 describes a rebuild that relabels Mudda/L1 and Nārāyaṇa/L1 rows from `two_pass_verified` to `classical_match`. If that relabel lands before the '4.1' run, a literal "only two-pass-verified rows vote" would drop those two systems too (ceiling 0.49) and change every stored '4.1' value — the opposite of what (a) is for. **(a) means the same rows keep voting**: the relabel changes the label on the same rows, not the evidence behind them, and the label is carried into every window's detail either way. The accepted set is therefore pinned by **name**, not by tier string.

**(b) — admit the honestly-labelled level-1 rows of the other five** — is **deferred, not refused**: it is to be taken up as its own decision for the governed `'5.x'` permission, with a per-(system, level) accepted set, the tier carried into every window, and **only after R-VOCAB-1** says what `classical_match` is worth for the daśā writers; Kālacakra stays out until a second check exists (DPT §"Recommendation"). It is **not** applied to '4.1' because it adds 86 relay-checked votes to a diagnostic whose only job is to measure what the old engine does.

**(c) — rescale the denominator to 0.66** — **rejected**: it multiplies every value by 1.52 and makes a third-missing prior look complete (DPT table). That is a number chosen for how it reads — CLAUDE §N.7 item 6.

**(d) — admit the deeper `single` levels** — **rejected**: ~86,000 unchecked rows; permission inflates and loses discrimination (DPT table; Stream A: "not neutral").

### 4.3 Frozen now
**This choice is recorded on 2026-10-02, before any '4.1' output exists** (DPT frontmatter: "No candidate was run"; FRZ §5: the freeze commits before any extract). **If, when the steward applies this, any '4.1' output already exists, STOP and report**: the choice can then no longer be pre-registered and DR-15(d) is engaged.

### 4.4 What the steward does
Fill FRZJ `dasha_plurality_tier_policy.version` with: `"(a) — accepted set by (system, level): vimshottari L1–L4 strict; mudda L1 and narayana L1 at their honest computed tier; all else unavailable; PR #2954 read_tier_policy @ <merge commit>"`, and record alongside it the **observed per-(system, level) tiers and row counts at freeze time** (the DPT table's figures, re-read read-only at the freeze). The '4.1' run must observe the same tiers and counts; if they differ, **stop** (DR-15(d)). Every served or reported '4.1' permission carries: "partial — 5 of 8 daśā systems unavailable (named); ceiling 0.66; diagnostic only".

### 4.5 How this response can be changed later
For '4.1': not after the freeze — a different policy is a different measurement, run once, never both ways (DPT §"Recommendation"). For '5.x': by the deferred (b) decision, as its own packet, under its own id.

---

## 5. Item 4 — the BPHS graduated-aspect re-read — `NRS-BPHS-REREAD-20261002`

### 5.1 What I verified myself this session
- **File:** `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt` — sha256 **`a51181de8272db15d135221bd9cd4e5e3135821207f221478d63eeb6d32a9ff9`** (matches RUL §5), **33,506 lines** (matches), 745,236 bytes.
- **Lines 16496–16502, verbatim** (line 16490 reads "Chapter 26", line 16493 the page number "255"):
  > 16496 `planets which I detail below. 3rd and 10th, 5th and 9th, 4th`
  > 16497 `and 8th and lastly 7th — on these places the aspects increase`
  > 16498 `gradually in slabs of quarters i.e 1/4, 1/2, 3/4th and full. The`
  > 16499 `effects (due to such aspects) will also be proportionate. All`
  > 16500 `planets aspect the 7th fully. Saturn, Jupiter and Mars have`
  > 16501 `special aspects respectively on 3rd and 10th, 5th and 9th, and`
  > 16502 `4th and 8th. The ancient preceptors have explained these which`

  This is exactly the text RUL §5 quoted and exactly what the frozen specification and oracle cite (`GOCHARA_DESIGN_SPECS_v1_4.md:820`; `GOCHARA_TEST_ORACLES_v1_4.json:429`: "ordinary aspects graduated ¼/½/¾/full at 3-10/5-9/4-8/7; specials full").
- **Lines 16605–16630:** the sphuṭa-dṛṣṭi Rules 1–6, as RUL §5 states (30–60: (angle−30)/2; 60–90: angle−60+15; 90–120: (120−angle)/2+30; 120–150: 150−angle; 150–180: 2×(angle−150); 180–300: (300−angle)/2; none between 300 and 30).
- **Served corpus, read this session:**
  - `hora_sara:PG20:C1` (śl.14): "The planets cast full aspect on the 7th from their position. The aspect is 3/4th on the 4th and the 8th houses. It is only half on the 5th and the 9th houses. A quarter glance is made on the 3rd and the 10th houses." Notes: Mars full on 4th/8th, Jupiter on 5th/9th, Saturn on 3rd/10th. **Confirms.**
  - `jataka_parijata:PG99:C1` (śl.30–31, via `read_chapter(jataka_parijata, 99)`): "all the planets cast a quarter glance at the 3rd and 10th houses, half a glance at the 5th and 9th, three quarters of a glance at the 4th and 8th, and a full eye at the 7th … Saturn is exceedingly powerful when he has his strong quarter glance, Jupiter … in his oblique or angular aspect, Mars is potent with his three quarter glance." **Confirms.**
  - `uttara_kalamrita:PG40:C2` (chunk begins mid-sentence): "…aspect on the fifth and ninth houses from himself. The other planets have only a half aspect on these houses from themselves. Mars has a full aspect on the fourth and eighth houses from himself. Others have a three-fourths aspect on…" **Confirms (partial chunk).**
  - `read_chapter(bphs, 26)` returns chapter-1 chunks (planet names, benefics/malefics) — the served BPHS **cannot** cite its chapter 26 by locator; RUL §5's L0 corpus-chaptering finding is **confirmed**.
  - Tool note for the L0 owner (not load-bearing): `find_verses_about` with a `text_ids` filter returned **0 results for every text**, including Hora Sāra and Jātaka Pārijāta whose chunks the unfiltered hybrid search and `read_chapter` then found. The filtered path looks broken.

### 5.2 What I could not verify
- The Sanskrit lines (16507–16510) are OCR-garbled in the local file; I read the translator's English only, as the earlier delegate did.
- I am not a person. Two independent agent sessions have now read the same hash-pinned lines and three independent served texts agree with them; that closes the **substantive** risk the governance item guards against (that the citation does not say what the spec claims). It does not make an agent's read a human's.

### 5.3 Response — not discharged by delegation; open as a formality; blocks nothing
The item asks for a **human** confirmation. Delegating "a human reads this" to an agent does not discharge it; it relabels an agent read as a human one, which is the kind of status-without-detector CLAUDE §N.8 forbids. So the item **stays open**, with two changes: (i) it is explicitly a **formality** — nothing in the campaign waits on it; (ii) it gets a **deadline: before D-FLIP**, because the flip is the moment the graduated-aspect convention this passage grounds becomes served truth for his chart.

### 5.4 The one-minute procedure (the owner's)
Either:
- open the source at the lines — one command the steward can paste for him:
  `sed -n '16496,16502p' /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt` — and read the seven lines; **or**
- read the seven quoted lines in §5.1 above (weaker: a hash-pinned agent transcription, not the source);

then write one dated line in the tracker: *"BPHS vol.1 lines 16496–16502 read; they say what the spec cites."* That closes the item. If the lines do **not** say what he expects, he says so, and the spec's citation becomes a Stream B finding.

### 5.5 How this response can be changed later
He may close it any day by the line above, or declare it moot by a dated ruling that he accepts the two agent reads as sufficient (his call to make, not mine to presume).

---

## 6. Everything else in NATIVE_OPEN_DECISIONS v1.10 — does it need an answer now?

| Listed item | Needs an answer now? | Why |
|---|---|---|
| **ND-NODE-VEDHA** (do Rāhu/Ketu obstruct) | **No.** | Ruled "undecided stays" with a named deadline — before qualified P2 scoring is scheduled for any `'5.x'` generation (RUL §2.5). No such scheduling exists; the first candidate is all-NULL. The deadline, producer (Stream B's corpus pass, then a human read) and the delegate's recommendation at the deadline stand unchanged. |
| **D-FLIP** | **No.** | Not due until J2 (NATIVE_DECISION_PACKET §D-FLIP). Conditions restated: a `'5.0'` generation **sealed** under §3 (verification rows by the separate job; seal approved by him per §3.3); every protocol v2.3 endpoint passes including T-honesty with a real (class, year) manifest; A5.7 gates pass; serving completeness and consumer routing done; the §2 disclosures rendered; migration 1236's authority guard relaxed by an explicit reviewed migration (RR11 §C2); the BPHS formality of §5 closed. **Not approved here.** |
| **D-T2** | **No.** | Due at J2, path by path, with B6.1 doctrine in hand. Untouched. |
| **Dispatch of the protected window** (act 9) | **No — and not approvable today.** | Codex round 10: step (a) BLOCKED by R10-1, R10-2, R10-3, R10-4, R10-7 (CDX10:227). Conditions: RUL §4 item 3 as amended by §2.6 above. |
| **The nine §3.6 acts** | **Answered** — §2. | |
| **Approval of each seal** | **Answered** — §3. | |
| **ND-DASHA-PLURALITY-TIERS** | **Answered** — §4. | |
| **BPHS human confirmation** | **Answered** — §5 (stays open as a formality, due before D-FLIP). | |
| "Implementation of the newly ruled numerical values is deferred until the review round returns" (IDX:12) | **Not his.** | A steward sequencing note; Codex round 10 confirms (CDX10:208). |

Nothing else in the index, in RUL §4–§5, or in RR11's owner-acts line (RR11:42) is waiting on him.

---

## 7. Still needs the owner in person (as short as honesty allows)

1. **Dispatch the protected migration window** (act 9) — when §2.6's conditions hold; the steward will tell him when they do.
2. **Provide and hold the seal-approver identity** (§3.3): create a dedicated approval account, or move `amonty84`'s token off every agent machine. One-time, ~10 minutes. Needed before act 5.
3. **Approve the live-gate proof** (§3.4) from his own device. One-time, ~1 minute. Needed before act 2b.
4. **Approve every generation seal** (§3), after reading the seal brief. Each time.
5. **Read BPHS lines 16496–16502 once** and write one dated line (§5.4). ~1 minute. Due before D-FLIP.
6. **Say "stop"** at any act boundary if a report reads wrong (§2.4 item 3). Optional, any time.
7. *(Later, not now)* ND-NODE-VEDHA at its deadline if no source is found; D-FLIP and D-T2 at J2.

Everything else in this file the steward may carry out.

---

## 8. Where I was genuinely uncertain (for the steward)

- **Roles before the window vs. the backfill route (§2.2a).** Codex offers both (CDX10:183). I chose roles-first because it is the rehearsed order and avoids a new migration + review + rehearsal; the cost is that two login-capable principals exist for the hours or days between creation and the window. I bounded that cost (same sitting as dispatch; the sealer created **without** a password until the human gate is proven; the verifier's password only in an IAM-bound secret). A stricter owner might still prefer the backfill route so that nothing exists until after the window; that is a legitimate choice and a one-line overrule.
- **The approver identity (§3.3).** Requiring a GitHub identity no agent can exercise is the only arrangement under which "the owner approved" has a real detector behind it. It costs him a small in-person task and puts a human step on the critical path before act 5. I could have accepted the weaker "procedural" arrangement with a written confirmation — but every channel such a confirmation could travel (tracker, email, chat) is one agents can also write to, so it would not be a detector. I chose the real check.
- **The relabel clause in §4.2.** PR #2954's description mentions a rebuild that relabels Mudda/L1 and Nārāyaṇa/L1 to `classical_match`; I found no fuller account of that rebuild in the briefs. If I have misread it and no relabel is planned, the clause is harmless (today's set is the same under both readings). If a relabel **is** planned, the clause is load-bearing and the steward should confirm with Stream A that PR #2954's policy yields exactly today's three systems after it.
- **The BPHS item (§5).** One could argue the owner's "answer everything on my behalf" instruction was meant to close this too, and that insisting on a human minute is over-literal. I kept it open because the item's whole content is the word "human"; closing it by agent would be the label-without-detector pattern this project has spent three campaigns removing. It blocks nothing, so the cost of being over-literal is one minute of his time; the cost of being under-literal is a false record.
- **Act 2a's `PASSWORD NULL` detail.** It is standard PostgreSQL behaviour that a NULL password cannot authenticate by password; I have not tested it against this Cloud SQL instance's authentication configuration. The runbook should verify on the disposable PG15 mirror first (one connection attempt that must fail), and if Cloud SQL behaves differently, acts 2a and 2b collapse back into one act performed after act 5 and the live-gate proof — which only delays the sealer role to after the window and re-opens R10-7's late-role case for the sealer's 1240 grants. The steward should check this before scheduling.

*End of NATIVE_RESPONSES_BY_DELEGATE v1.0. Responses in this file are applied by the campaign steward; they are never edited in place — a change is v1.1 with a changelog.*
