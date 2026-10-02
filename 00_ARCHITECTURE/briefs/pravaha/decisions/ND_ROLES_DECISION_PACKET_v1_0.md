---
artifact: ND_ROLES_DECISION_PACKET
version: "1.0"
status: "FOR THE NATIVE — nothing here is decided. ND-ROLES is a REAL BLOCKER of step (c) (the first '5.0' candidate build): without separate verifier and sealer principals the database cannot tell a builder-written 'independent verification' from an independent one, and Codex requires builder refusal and removal of the builder's verification-write capability (PC-1/PC-4)."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 (steward M20261002T035035-861e)
evidence_rule: "facts about the production database are from READ-ONLY queries of 2026-10-02; facts about governance and deployment from the repository files cited; nothing was changed anywhere"
---

# ND-ROLES — who holds the "verified" stamp and the "published" seal?

## In plain words
The build writes thousands of rows. Two later acts must be done by someone **other than the builder**, or they mean nothing:
* **Verification** — an independent re-derivation that says "these windows are exactly what the inputs imply". If the builder can write that stamp itself, the stamp proves nothing.
* **Sealing** — the act that freezes a generation as published (the first step toward the flip, which is yours alone).
Today **neither principal exists in a usable form**, and the builder is even *allowed* to write the verification stamp (migration 1206 §7 grants it). You are asked **how the pipeline gets its two extra keys**: who holds them, where the passwords live, and what we change in the database and in the deployment gates. Each option below says what has to be built, who does it, and what it costs.

## Facts (production, read-only, 2026-10-02; PostgreSQL 15.18)
| role | login? | what it is today |
|---|---|---|
| `amjis_app` | yes | owns every gochara object; runs migrations; **no** CREATE except inside a protected window |
| `data_plane_builder` | yes, NOINHERIT | **the pipeline's login** — Cloud Run runs as service account `data-plane-builder-runtime@` with secret `data-plane-builder-db-url` (`deploy.yml:933–934, 2192–2193`) |
| `data_plane_migrator` | yes | member of the three owner roles; used only by protected windows |
| `data_plane_verifier` | yes, NOINHERIT | **exists**, but is a *read-only L1 verifier*: SELECT on `chart_dashas`, `chart_facts`, `_migrations_applied`; **no privilege at all on any `ka_gochara_*` table or function**; **no service account and no secret for it in the repo's secret-isolation gate** (`data-plane-secret-isolation-preflight.ts` defines only the builder's) |
| `gochara_sealer`, `gochara_verifier` | — | **do not exist** |
| `role_*` (jobs, orchestrator, sidecar, web_serve, ledger_write) | no (NOLOGIN, inherit) | application permission bundles |
| membership edges among the six controlled data-plane roles | — | exactly three: the owner roles → `data_plane_migrator` |

## The governance rules any option must respect (each is enforced by a deploy gate)
1. **Exact-membership gate (DP-SD-018, `data-plane-ownership-status.ts`; `normalizeDataPlaneMemberships` in the preflight).** Any membership edge that involves `data_plane_builder`, `data_plane_verifier` or `data_plane_migrator`, other than the three owner → migrator edges, is *drift*: the preflight **revokes** it and the status gate **fails the deploy**.
2. **Name gate.** A role named `data_plane_<anything>` outside the six is rejected ("unknown data-plane principal collision"). New principals must not use that prefix.
3. **Secret isolation (GCP IAM gate).** A runtime job may bind only its own secret; every additional database credential needs its own service account, secret, IAM binding and an extension of `data-plane-secret-isolation-preflight.ts`.
4. **Production default privileges** revoke PUBLIC EXECUTE on everything `amjis_app` creates, so each principal needs explicit table *and* function grants (the live suites derive them).
5. **Role creation is not a migration.** `amjis_app` has no CREATEROLE; creating a login role is an administrative act (the ownership-admin path, `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL`), not something a numbered migration can do.

## The options
| | **A. Separate credentials, no role switching** (recommended) | **B. The pipeline switches role inside its own session** | **C. One job holds two logins** | **D. Keep today's arrangement, disclose it** |
|---|---|---|---|---|
| **How the pipeline acts as verifier / sealer** | **Verifier:** a *separate verifier job* under its own service account and secret logs in as the verifier principal. **Sealer:** a *separate sealer login* held in an **approval-gated environment** (the same pattern as the protected migration window) — the seal is the publication step, so a human approval belongs on it, not an unattended job. | `SET ROLE gochara_sealer` / `gochara_verifier` from the builder's own login (`data_plane_builder`, NOINHERIT — `SET ROLE` still works for a member) | the builder job's process is given a second and third database password and opens a second connection as the verifier / sealer | nothing changes: the builder writes the verification row; the seal is run by whoever has a suitable login |
| **Membership / who grants it** | none | `GRANT gochara_sealer TO data_plane_builder` by `postgres` (Cloud SQL admin) | none (but two more secrets bound to the builder's service account) | none |
| **Secret** | verifier: new secret `…-verifier-db-url` + its own SA; sealer: new environment secret with required reviewers | none (same login) | two new secrets bound to the **builder's** SA | none |
| **Separation of duties at the database** | **Real**: three logins, three privilege sets; the builder cannot write a verification row or seal | **Nominal**: the same login can become any role — the database cannot tell who acted | **Weak**: one process holds all three keys; a defect or a compromise of the builder job holds them all | **None** |
| **Collides with a gate?** | No (new names outside `data_plane_`; no membership edge). Needs the secret-isolation gate **extended** for the verifier SA | **Yes — DP-SD-018**: the new membership edge is reverted by the preflight and fails the status gate; both scripts would have to be amended with an allowlist | **Yes** — secret isolation (builder SA may bind only the builder secret) | No |
| **What must be built** | (1) admin act: `CREATE ROLE gochara_sealer LOGIN NOINHERIT` (+ optionally `gochara_verifier`, or reuse `data_plane_verifier` — see below); (2) a grants-only routine migration; (3) service account + secret + IAM binding + a verifier Cloud Run job + preflight extension; (4) an approval-gated sealing workflow with its environment secret; (5) the live suites' `verify` helper switched to the verifier role | (1) admin act: the roles and the membership grants; (2) the grants migration; (3) amend two governance scripts; no new job/secret | (1)–(2) as A; (3) amend the isolation gate to allow three secrets on one SA | nothing; but PC-4 stays **unmet** and step (c) cannot claim database-level independence |
| **Cost / owner** | infra + ops work (steward / owner of deploy); ~4 artefacts; no code in the gochara writers beyond choosing the connection | small build, **governance weakening** | medium, governance weakening | none, **but blocks the milestone** |

### Reuse `data_plane_verifier`, or a new `gochara_verifier`? (inside option A)
* **Reuse:** one fewer principal, the login, SA-able secret path and the gates already know it. But it is defined (and its ACL asserted) as a **read-only L1 verifier**; making it write verification rows changes the meaning of a governed role and must not break its protected-table assertions (they cover only the L1/L2 protected sets, not `ka_gochara_*`).
* **New `gochara_verifier`:** clean purpose, untouched governance set, but a new login/secret/SA and a name outside `data_plane_`. **Recommendation: new `gochara_verifier`** (least surprise for the governance gates), unless you prefer the smaller change.

## What a minimal provisioning migration contains (option A)
A **grants-only, routine, owner-run** migration (proposed number from the 1230–1249 block, e.g. 1235; role creation itself is the admin act above):
* `GRANT USAGE ON SCHEMA public` and `SELECT` on the verification read set (inventory, snapshot, pin, obligation, interval, records, windows, window membership, coverage, `chart_facts`, `chart_dashas`) **to the verifier**; `INSERT` (and pre-seal `DELETE`) on the verification tables (1206's `ka_gochara_search_inventory_verification` and Stream A's 1240 table) **to the verifier only**; `EXECUTE` on the functions those inserts' guards call.
* **To the sealer:** the table/function grants the live suites already grant it (SELECT on the seven tables the seal reads, `INSERT` on `ka_gochara_generation_seal`, `UPDATE` on `kala_gochara_publication`, `EXECUTE` on the 23 seal-side functions, including 1232's two).
* **From the builder:** `REVOKE INSERT, DELETE ON ka_gochara_search_inventory_verification FROM data_plane_builder` (see the next section) — and **never** any privilege on 1240's table.
* Role-existence guards for the sealer/verifier (the roles are created by an admin act that may run after the migration), **plus a post-check that prints which principals were found** — a grants migration that silently granted to nobody is the standing hazard (`CLAUDE.md §N.4`).

## What happens to 1206 §7's builder grant on inventory verification, per option
1206 is **not yet applied in production** (it waits for the protected window), so its §7 can still be corrected **before first application**.
| option | 1206 §7 builder `INSERT/DELETE` on `ka_gochara_search_inventory_verification` |
|---|---|
| **A** | **Removed.** Two ways: **(i) edit §7 of 1206 before it is first applied** (one grant line; cleanest — there is never a moment when the builder holds the capability; but PR #2867's head moves and Codex re-reviews a one-line grant change); or **(ii) leave 1206 as accepted and `REVOKE` in the grants migration** (no re-review of 1206, but the builder holds the capability from the window until that migration is applied — close the gap by ordering the grants migration immediately after the window). The live suites' `verify` helper (today run as the builder) is switched to the verifier role either way. |
| **B** | **Kept** (the builder session may switch to the verifier role anyway, so removing it protects nothing the role switch does not undo); PC-4 is nominally met only. |
| **C** | **Removable** (the second login does the verifying), but the same process holds both keys, so the independence gained is procedural. |
| **D** | **Kept**; PC-4 unmet; the disclosure must say the verification stamp is not database-independent. |

## Questions for you
1. **Do you accept that verification and sealing are held by principals separate from the builder, at the database level?** *(Recommended: yes — option A.)*
2. **Who holds the seal key?** An **approval-gated operator workflow** (recommended: the seal is the step before your flip) / an unattended job / you personally.
3. **Verifier:** an automated separate job with its own service account and secret (recommended) / run by hand when needed. And: **new `gochara_verifier`** (recommended) or reuse `data_plane_verifier`.
4. **1206 §7:** edit it before its first application (recommended) or revoke afterwards.
**Until you decide:** the first candidate can be built and held, but it **cannot be verified or sealed with database-level independence**, and Codex's PC-1/PC-4 evidence cannot be produced.

## What I need from the infrastructure owner once you choose A
(1) the admin step creating the login role(s); (2) the service account, secret and IAM bindings for the verifier job; (3) the isolation-gate extension; (4) the approval-gated sealing workflow and its environment secret. Stream B will author the grants migration and extend the rehearsal script's S4 matrix; Stream A's writer must connect as the verifier for the verification step and Stream C can rehearse the whole matrix on a disposable PostgreSQL 15 first.
