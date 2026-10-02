---
artifact: NATIVE_DIRECT_RULINGS_20261002
version: "1.0"
status: "RULED — typed by the native himself in the steward's window on 2026-10-02; relayed by the steward (tracker M20261002T134159-2292) and recorded here verbatim in substance. These rulings OVERRIDE the delegate's documents (NATIVE_RULINGS_BY_DELEGATE_v1_0.md, NATIVE_RESPONSES_BY_DELEGATE_v1_0.md) wherever they differ. Nothing in the delegate's documents is edited; this file supersedes them where it speaks."
recorded_by: "Stream B (Śāstra), item B6.0"
---

# The native's direct rulings — 2026-10-02

| # | ruling | overrides | where it lands |
|---|---|---|---|
| **1** | **SQL admin route = OPTION A.** The one-shot, **reviewed** GitHub workflow, using the **existing governed ownership-admin secret**, run under the owner's credentials by the steward. **Authored now as a DRAFT PR (HOLD).** `workflow_dispatch` only; runs the reviewed `CREATE ROLE` SQL for `gochara_verifier` and `gochara_sealer` over the ownership-admin path (never `gcloud sql users create`; post-check `pg_has_role(…,'cloudsqlsuperuser','MEMBER') = false`); generates passwords **inside the run** and writes the verifier's straight to Secret Manager (never echoed, masked, no artifact); sealer created per the runbook's `PASSWORD NULL` / fallback rule; prints only non-secret verification facts; idempotent, refuses if the roles already exist; **removed or disabled in a follow-up PR after use**; tests/lint for the workflow file; **Codex reviews it before it is ever dispatched.** | delegate's open item (runbook §7.1) | runbook §7.1, acts 1/2a; the workflow PR (draft) |
| **2** | **SEAL APPROVAL: the SAME account is used — no separate approver identity — and the native has authorised the STEWARD to access his account and approve seals on his behalf.** This **overrides NRS-SEAL-APPROVER ("no delegate ever")**. | NRS-SEAL-APPROVER-20261002 (§3 of the responses file) | runbook §5.3 and act 5; packet claim section |
| **3** | **TENTH ACT: YES** — the deploy principal may hold `roles/iam.serviceAccountUser` on the verifier service account **only**. | (was an open item) | runbook act 10 |
| **4** | **BPHS graduated-aspect re-read: discharged by the owner's delegation to the steward.** The steward read the project's local source file on 2026-10-02 — `bphs_vol1_rsanthanam_djvu.txt`, sha256 `a51181de8272db15d135221bd9cd4e5e3135821207f221478d63eeb6d32a9ff9`, 33,506 lines, **lines 16496–16502** — and the text is as quoted in NATIVE_RULINGS §5: quarter at the 3rd/10th, half at the 5th/9th, three-quarters at the 4th/8th, full at the 7th; Saturn, Jupiter and Mars special aspects on 3/10, 5/9, 4/8. **Stated as what it is: an agent's read under the owner's explicit instruction, not a human's.** | the "due before D-FLIP" open formality | NATIVE_OPEN_DECISIONS; runbook §7 |

**Timing is unchanged:** no credential act is executed until the window pre-conditions hold **and** the steward tells the owner it is starting. Lower priority than anything round 11 returns.

## What ruling 2 changes, honestly
The seal approval is **no longer an independent human check.** The gate's independence between "the one who dispatches" and "the one who approves" is gone: the steward can dispatch and approve under the owner's account. What remains, and what the approval now rests on:
1. **the database gate** — the combined candidate gate = 0, every window `VERIFIED` by the separate verifier job, the runner's recorded code pinned to the manifest;
2. **the sealer step re-computing the gate** against the briefed digest and refusing on any difference (a stale brief refuses);
3. **the steward approving ONLY when the seal brief shows gate = 0 and m of m `VERIFIED`**, and **reporting each approval to the owner immediately with the brief attached.**

The claim "a human approved this seal" must not be made on the strength of the approval click alone; the supportable claim is (1)–(3).
