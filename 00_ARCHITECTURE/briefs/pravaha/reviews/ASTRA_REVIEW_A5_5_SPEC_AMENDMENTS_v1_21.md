---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.21"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "019f445b9 (campaign/pravaha)"
authority: "Review only; authorizes nothing."
---

**Is the protected window NOW EXECUTABLE AS PACKAGED with only operational acts remaining — NO.** The revised page still contains contradictory STOP rules and an impossible intermediate qualification step. The previously accepted SQL, composition and writer code remain outside this review.

Paths below are under `00_ARCHITECTURE/briefs/pravaha/`:

- **C:** `runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md` — v1.10.
- **R:** `runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md` — v1.21.

| Finding | Closure | Evidence / remaining correction |
|---|---|---|
| R21-1 | **CLOSED** | C:21,23 install #2981 before its proof, including qualification, freeze exception and drain. |
| R21-2 | **PARTLY** | Pins and synchronization are present; C:12,24 still impose impossible ordering and retain obsolete conflict instructions. Amendments 1–2. |
| R21-3 | **CLOSED** | R:300 states the two-table predicate, retention limits and every-dispatch disposition/removal commitment. `runbooks/rehearsal/registry_1243_readback.sql:19–20` corrects the continuity expectation. |
| R21-4 | **PARTLY** | Act-9 identity is corrected. R:283 still says the verifier/sealer hold “NO grants.” Amendment 4. |
| F-R21-1 | **PARTLY** | C:24 checks draft/base status only immediately before each individual merge; the required all-remaining-PR gate and `UNKNOWN` handling remain incomplete. Amendment 2. |
| F-R21-2 | **PARTLY** | C:14 names both RED shapes, then its mandatory recording rule and C:24 STOP cell reject the second. Amendment 3. |
| F-R21-3 | **PARTLY** | C:25 correctly splits window failure from later failure, but omits the requested routine/deployment readbacks and explicit recovery dispatch. Amendment 5. |
| F-R21-4 | **PARTLY** | Current pins, identity and monitor wording are corrected; C:24 still instructs resolution of the old #2867 workflow conflict. Amendment 2. |
| F-R21-5 | **CLOSED** | C:19 supplies the pre-read command and requires repetition immediately before row 8. The packaged note distinguishes the informational `av_qualifier` count from a forward refusal. |

Exact remaining amendments:

1. **C:12,24 — place qualification at executable stages.** Replace the blanket “Before the sitting (all TRUE)” with stage-specific prerequisites: synchronization follows row 4 and precedes the first train merge. Replace the full ten-file check **after EACH merge** with:

   > After #2867 and #2919, check the seven and nine landed manifest entries respectively and run the executing selection test with `WINDOW_MERGE_CONTROL` unset. Repeat full qualification on the synchronized writer head, including its implementation lock. After #2999, require all ten hashes and `WINDOW_MERGE_CONTROL=1` on actual merged main before row 8.

   #2867 lacks 1232/1233/1240; #2919 lacks 1240. The current full-mode check necessarily fails at those intermediate stops.

2. **C:24 — complete readiness and remove obsolete conflict instructions.** Replace “nothing is un-drafted earlier” with:

   > Before the first train merge, mark every remaining draft train PR ready. Before that merge and after each squash, read `baseRefName,isDraft,mergeable,mergeStateStatus` for every remaining PR; require `main`, `false`, `MERGEABLE`. `UNKNOWN` means re-poll.

   Delete the asserted current #2867 workflow conflict. Its recorded head, #2919’s head and #2961’s head have the **same `deploy.yml` blob**. Require inspection of actual conflicts instead.

3. **C:14,24; R:276,316 — use one automatic-run rule.** Replace the “each run must show the `1204` refusal” requirement with:

   > Record either named RED shape. For non-green CI, the outcome gate fails while change detection and migration/deployment jobs are skipped; the failing gate itself is not skipped. Re-run that CI with `gh run rerun <ci-id>` and obtain green CI plus the recorded protected-file refusal before the next train merge.

   Replace “no routine deploy between” with “automatic runs are required and recorded; no protected migration or service deployment may occur.”

4. **R:283 — reconcile grants and scheduling with C:28,31.** Replace the conflicting passage with:

   > The 1206/1240 grants already exist and are positively verified. Only 1241’s remaining ACL closure waits for SETTLED-1. Setup is forbidden during S-L1; rows 7–9, including qualification, finish before W1 or start after SETTLED-1.

5. **C:19,25; C:7 and R:14 — finish the split failure procedure.** Add explicit ledger presence/absence for **1255, 1300 and 1301**; record the general runner’s `Applied:` lines, all four deployment-job results and the earned-outcome result. Replace “then decide” with:

   > Qualify the applied window first; repair the later failure through a reviewed forward fix, then re-dispatch without the window flag.

   Qualify the introductory “do not fix forward” prohibition as **“no unreviewed repair; follow row 8’s failure branch.”**

6. **C:21,24 — repair command execution.** Quote the API argument:

   `gh api 'repos/Marsys-Technologies/Madhav/contents/.github/workflows/gochara-seal-gate-proof.yml?ref=main'`

   The unquoted command fails under the supplied zsh. Enclose the `cd platform && …` test invocation in parentheses so subsequent repository-root paths resolve correctly.

Row 9’s positive privilege readback, `CREATE=false`, and both W5/W6 comparison directions are explicit. Both 1235 and 1241 remain outside this window. Act 9 consistently belongs to the AI steward under the owner’s ruling.

Local remote refs agree with the referenced branch/head identities. Live PR base/draft/mergeability was **not verified**: GitHub API access failed. No files were written and no production database was accessed.

