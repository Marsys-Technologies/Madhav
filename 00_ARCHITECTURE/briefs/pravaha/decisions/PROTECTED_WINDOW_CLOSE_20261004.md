---
artifact: PROTECTED_WINDOW_CLOSE_20261004
version: "1.0"
status: RECORD — the Gochara protected migration window is APPLIED and qualified; open list in section 7
date: 2026-10-04
written_by: "Stream B (Śāstra), session madhav-8b, at the steward's request (M20261004T121741-3a53, WINDOW-DONE)"
audience: "the owner, and any later session that must know what was done, by whom and what is still open"
evidence: "/Users/Dev/pravaha/run/sitting-20261004/{pre-window,pre-dispatch,post-window,manual}; /Users/Dev/pravaha/run/sitting-20261003/{pre-window,manual}; GitHub Actions runs named below"
changelog:
  - "1.0 (2026-10-04): first version."
---

# The protected window — closed

## 1. What was applied, when, by whom
- **Applied:** `1204_gochara_av_qualifier_object_role.sql`, `1206_gochara_search_inventory_completeness.sql`, `1232_gochara_search_moon_scope_domain.sql`, `1233_gochara_p1_period_anchor.sql`, `1240_gochara_window_verification_gate.sql`, in that order, at **2026-10-04 11:50:55–11:51:01Z** (ledger `applied_at`; sha256 prefixes `a0b267f7…`, `941c79f5…`, `f2ef6406…`, `958b9117…`, `05a8f897…`, equal to the committed manifest). `1153`–`1157` were already applied (3 Oct, 22:35Z) and were hash-checked and skipped. No `1241`.
- **By whom:** the **steward**, dispatching `deploy.yml` with `gochara_contracts_schema_migration=true` **under the owner's account**, on the owner's ruling 2 of 2026-10-03 (`NATIVE_DIRECT_RULINGS_20261003.md`); dispatched 11:44:50Z, **run 37199771216**, on `main` **`8865b2d4e4622ac9c02ccd1d590dc6e54545cdd6`**. The run: protected job success (temporary capability granted, window applied, capability revoked), general runner success with no `Applied:` line (nothing else pending), Build & Deploy Pipeline Job Image / Sidecar / Web success, MCP skipped by change detection, earned-outcome success. Ledger 933 → 938.
- **Train before it** (squash merges through the merge queue, one at a time, each with its stage check): #2867 → `fc1831f47` (10:02:29Z), #2919 → `0c83245d8` (10:41:10Z), #2999 → `8865b2d4e` (11:16:38Z). Heads at merge: #2867 `617633a9a`, #2919 `c62afd5a8`, #2999 `17115720c` (tree `1345c1d4…`, byte-identical to the reviewed re-pinned head `0acd0146b`). Earlier controls: #2961, #2963, #2981 (22:36–22:43Z on 3 Oct), #3115, the 1302 revoke, Suvarṇa's S-L1 migrations.
- **Qualification:** row 9 was qualified twice independently (the steward's runner phase, and Stream B's own read-only queries): ledger exactly +5 with the right hashes; `amjis_app` and the three Gochara roles hold no CREATE on `public`; no `ka_gochara_*`/`kala_gochara_*` object owned by anyone but `amjis_app`; the 92-grant privilege readback returns zero rows; no `ka_gochara_*` function executable by PUBLIC (87 checked, effective ACL including the default-ACL case); trigger manifest: expected-minus-production empty, production-only exactly the two baseline legacy triggers, nine `ka_gochara_boundary_*` additions; the four-relation guard inventory t/t/t; W2a/W2b/W2c identical to the pre-window re-take. Rehearsal on the final main bytes: 47 passed / 0 failed / 0 findings, trigger manifest equal to the committed file.

## 2. Deviations and incidents of the two days (3–4 October)
1. **Stale administrator secret (row 5).** At the first step needing the database administrator's login (creating the two new roles) our GitHub environment secret `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL` was rejected; nothing was created, the temporary capability was removed, nothing else changed. The administrator login itself worked from Secret Manager; only our copy was stale. Resolved by the steward refreshing the secret from Secret Manager on the owner's word (rotation of the `postgres` password was ruled out); afterwards the secret was NEUTRALISED to a throw-away value (01:04:49Z) and **must be refreshed again on the owner's word before any further use** (act 2b). Record: `SITTING_PAUSE_ROW5_20261004.md`.
2. **Environment branch-policy finding (row 6).** The live gate proof showed the environment policy "protected branches only" admits every branch in a repository without classic branch-protection rules, so an off-main dispatch was not refused. `gochara-seal` was repaired (custom branch policy `main`; reviewer; no secrets) and re-proved; `data-plane-production-cutover` was NOT changed — the owner's decision. Record: `ENVIRONMENT_BRANCH_POLICY_FINDING_20261004.md`.
3. **Declared control-plane exception (Firebase agent).** Act 7's isolation preflight refused because Google's Firebase management agent holds `resourcemanager.projects.setIamPolicy`; the steward declared the single exact triple in `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` (23:43Z, 3 Oct). Codex: ACCEPT of the allow-list change (PR #3119, confined to the verifier-control gate) with the residual risk stated verbatim; the PR stays draft until the owner confirms. Record: `DECLARED_CONTROL_PLANE_EXCEPTION_20261003.md` (v1.3).
4. **Accidental deletion of that variable.** At 05:48:58Z the variable was deleted by Stream B's own tracker report (a back-quoted command inside a double-quoted shell string); every routine deploy failed its isolation step until the steward restored the same triple at 09:08Z (about three hours; Suvarṇa's migration 1256 waited). Standing rule: report text never goes through the shell inside double quotes. Detail in the decisions note above.
5. **The 1219 change-scope guard.** A test armed on any change that adds a migration failed every later PR adding a different number, which would have blocked the train; fixed by #3115 (the guard now binds only a change that adds 1219) and re-checked on every real merge ref of the train (18/18).
6. **Stage-2 shape B.** After #2919 merged, main CI was red with exactly one failing job (the non-required DB-integration job; 23 × `42501` on `ka_gochara_search_inventory_verification`) so the automatic deploy run failed closed at the earned-outcome gate with everything else skipped. Recorded as shape B under a one-stage exception (conditions: shape A recorded after #2867; the same job green on the #2999 head; fully green main CI and shape A on the final main). **Corrected cause (Codex):** a stale builder-role setup in the Moon-domain suite (its `verify()` inserted as the builder), fixed in #2999 — NOT missing 1240 grants as first diagnosed. Final main: CI 37198181060 fully green; automatic run 37199035356 = shape A (the 1204 refusal, all four deploy jobs skipped). Page v1.23.
7. **Conflicts after the first squash.** The #2867 squash left #2919 and #2999 conflicting in four files (migrate.ts, ci.yml, two unit tests) because they extend the same lines; resolved to the PR side with the proof that the result equals main plus each PR's own delta (and, for the a53 branch, a tree byte-identical to the reviewed head).
8. **Dasha re-pin at SETTLED-1** (build `75524b3e…`, lock `fcfb6827…`): `DASHA_REPIN_SETTLED1_20261004.md`.
9. **Runner tool defect found at row 9:** `P9-public-execute` names the pseudo-role in upper case (`PUBLIC`) and fails with "role PUBLIC does not exist"; the check was replaced by a manual read-only query (and confirmed independently). To fix in the runner (lower-case `public` / the ACL form).
10. **Finding outside the window:** 188 other functions in schema `public`, owned by `amjis_app`, are executable by PUBLIC (default function ACL) — older than this window, not `ka_gochara_*`; reported for a separate decision.

## 3. Chart-data and build state
No Gochara build, verification, brief, dry run or measurement on chart `482012f1…` was performed in production by this window; those remain held until the steward lifts them (the small test build has its own preconditions to review first).

## 4. Production facts to remember
The production windows table carries its own generation guard (`public.kala_gochara_generation_guard()` via `trg_kgw_generation_guard_row` / `_truncate`), STRICTER than migration 1071's fresh-path guard: it refuses UPDATE/DELETE of generations `v1` and `3.0` and TRUNCATE whenever such a row exists, unless `app.allow_protected_sweep_rewrite=on`. Its definition was captured read-only on 4 Oct (Stream B scratchpad, sha prefix `8ad929dc…`) for the C55 test.

## 5. Observed behaviour worth carrying forward
`ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md` §4.1 (v1.26): from the first governed (`'5.0'`) manifest onward, 1240's publication statement trigger takes the canonical chart's lock for every UPDATE/DELETE on `kala_gochara_publication`, so legacy builds of other charts will wait on it and are refused at REPEATABLE READ (C55, PR #3124).

## 6. Where the evidence is
`/Users/Dev/pravaha/run/sitting-20261004/{pre-window,pre-dispatch,post-window,manual}` (this window); `/Users/Dev/pravaha/run/sitting-20261003/…` (the first half); campaign branch `campaign/pravaha`: `PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md` v1.24, `POST_SETTLED1_SEQUENCE_v1_0.md`, the decisions notes cited above, and the reviews of Codex and Fable.

## 7. Open list (nothing here is authorised by this record)
1. **1241 v7** (PR #2949): verifier/sealer ACL migration — routine, after the window; its ACL closure waits for SETTLED-1 (now satisfied) and review.
2. **L1 read ACLs** for the verifier and sealer (the data-plane ACL owner's step).
3. **Act 2b** — the sealer's password behind the gate — needs the admin secret **refreshed again on the owner's word** (it holds a throw-away value).
4. **The verification job** (act 6 / 6b) and acts 12–14 (log view, execute, proxy rights).
5. **Function migration 1235** (the SECURITY DEFINER evidence function; PR #3018, HOLD): protected-class, needs CREATE on `public`, its own later dispatch.
6. **C53 / PR #3119** (Firebase agent allow-list) — draft until the owner confirms the exception with the residual-risk sentence in front of them; then merge, deploy, delete the declared variable, re-prove.
7. **Cutover environment branch policy** (`data-plane-production-cutover`) — owner's decision.
8. **Fable follow-ups A2–A4** (stale row-id comments, the generated test's generator claim, golden regeneration) and A1 (comment in a production script).
9. **Improved re-pin tool** (non-Z forms, wrapped ids, wider scan; PR #2903 improved branch) and its final Codex pass.
10. **C52, C54 (PR #3120), C55 (PR #3124), C57** (the 18 legacy reds).
11. **Runner tool defect** (upper-case PUBLIC) and the **188 PUBLIC-executable older functions** as a separate finding.
12. **Small test build** (Ruling 3, ~5 %) and the full build and seal after Suvarṇa's elevation — preconditions to be reviewed and the hold on chart `482012f1` lifted by the steward first; before the first governed manifest, re-run W1/W2 and tell Suvarṇa about the lock (POST_SETTLED1_SEQUENCE row 8a).
