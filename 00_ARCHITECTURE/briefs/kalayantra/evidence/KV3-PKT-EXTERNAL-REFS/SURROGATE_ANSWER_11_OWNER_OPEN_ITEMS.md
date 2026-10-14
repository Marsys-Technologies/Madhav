<!-- Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_11_OWNER_OPEN_ITEMS.md -->
<!-- Original sha256: 8d7bf3dd0a8ae86eae83d3d9cf39260254fa639dd9d58e15605124fdfa4c4779; date: 2026-10-14 -->
# Owner-surrogate answer 11 — every item that was waiting on the owner

Authority: the owner, just now: [REDACTED_OWNER_PERSONAL_INSTRUCTION] This delegates the decisions; it does not lift his NEVER list (no merge to main or a shared branch; no production; no credential read or print; no edit of the owner-decisions file or permission settings; no Suvarṇa integration branch or ri02). Where an item needs one of those, it stays with him and the one line he must say or type is given. Read-only; sources: the morning list (16 entries), hand-over state `HANDOVER_STATE_20261013T0526Z.md` ("Needs owner"), `PLANNER_STATE.active.owner_*`, answers 01–10.

Paths: `M` = `/Users/Dev/Vibe-Coding/Apps/Madhav` · `R` = `/Users/Dev/kalayantra/run` · `W` = `/Users/Dev/worktrees.noindex/madhav/claude` · `A` = `origin/kalayantra/kv3-b-assembly-all`.

---

### 1. The 28 superseded pull requests (27 `kalayantra/kv3-b-*` + #3283)
**DECISION** — Close them unmerged, with a comment; keep their branches. Closing is a GitHub write but not a merge, not production, not a credential: within the delegation.
**Cockpit now** — for each PR: confirm its head is contained in the assembly (`git -C M fetch origin && git -C M merge-base --is-ancestor <headRefOid> A`); only then `gh pr close <n> --comment "Superseded: this piece was independently reviewed and installed from the private assembly branch kalayantra/kv3-b-assembly-all (B-2, 2026-10-13); never merged by design (plan D-9). Branch kept."`. A PR whose head is not contained stays open and is listed. #3438, #3441 (the planner's own) and #3480 (K3-1b, real work) stay open.
**Not delegable** — nothing.
**Owner line** — 28 old pull requests of now-installed pieces are being closed unmerged; nothing of yours is merged.

### 2. History of the pushed branch (six words of your instruction file, local paths, in older commits)
**DECISION** — Leave the history. A force-push would rewrite the commits the installation receipt binds (`components_commit`, the bundle commit, the campaign checkout at that head); every base-containment check would then fail. The content is low-sensitivity (no secret, key or account detail) and the current commit is clean.
**Cockpit now** — one line in the privacy log naming the commits; nothing else.
**Not delegable** — nothing.
**Owner line** — six harmless words and some folder names stay in old commits of a private campaign branch; rewriting would break the installation's own bookkeeping, so they stay.

### 3. The local branch `kalayantra/kv3-b-qualify-codex` (unsanitised real-run fixtures; never pushed)
**DECISION** — Delete it without an archive. The sanitised equivalent is pushed in the assembly; the only difference is the identifiers, which must not be preserved — the "bundle before deleting" rule exists to prevent lost work, and here the loss is the point. Branch deletion is not on the NEVER list.
**Cockpit now** — `git -C M worktree list | grep qualify-codex` → remove that worktree first (`git -C M worktree remove <path>`); `git -C M ls-remote --heads origin kalayantra/kv3-b-qualify-codex` must print nothing; then `git -C M branch -D kalayantra/kv3-b-qualify-codex`. Do not run `git gc --prune`.
**Not delegable** — nothing.
**Owner line** — the local branch with your account identifiers is deleted; nothing of it was ever uploaded.

### 4. The executor restart (11 queued read-only checks; six merged items cannot close)
**DECISION** — Stays with the owner: the command sources the credential file, and the process it starts holds the production sign-in. The cockpit may not read, print or load that file.
**Cockpit now** — before he types it: list the 11 requests in `R/ops/requests` with their operation kinds, confirm each is a read-only readback the installed `fleet_live/executor_ops.json` has `enabled: true` for, and put that list in front of him; nothing executes until he starts the process. (Note: `fleet_live/executor.sh` is now the installed v3 script; the queued requests must be in its accepted form — the cockpit checks that too.)
**Not delegable** — the credential.
**Owner line** — in Terminal: `source ~/.config/kalayantra/executor.env && /Users/Dev/kalayantra/fleet_live/executor.sh up` — then the eleven read-only checks drain and six finished items close.

### 5. Doctrine and product readings
**5a. K3-1b roster** — **DECISION:** already ruled (answer 02): vedha, bhāva-destruction (Uttara Kālāmṛta PG77), dusthāna-lord-in-own-house (Phaladīpikā XV 27–29), bādhaka for movable lagnas (BPHS ch. 50 vv. 20–21, live only once served); the four legacy detectors retired. **Cockpit now:** hand answer 02 to the K3-1b packet; the three source mappings are technical bindings to the observed columns (answer 05). **Owner line:** your four obstruction checks are the cited ones; nothing uncited is kept.
**5b. K7-3 stored-tier pins** — **DECISION:** technical, not doctrine: the cockpit produces the per-view pin table from the ledger evidence (tiers exist on activation/darshana/jivana_parva/avadhi candidates; none on jury, issued_forecast, taranga, obstruction — declare "no tier; D(W) witness signature" there). **Owner line:** nothing for you.
**5c. L0-M v.88** — **DECISION:** encode both readings as separate rows marked by source — the commentary's AND-plus-intervening-benefic row (`extraction_context = tika_commentary`) and the reconstruction's OR row (`extraction_context = mula_reconstructed`), each with its locator and verbatim passage. The evaluator cancels when either applies and names the row; when the two readings disagree on a candidate the doṣa reads `cancellation_unassessed`, reason `readings_disagree`, both rows cited. No reading is invented; retiring one row later is a one-line change. **Cockpit now:** unblock the L0-M packet with this rule. **Owner line:** both readings of verse 88 are stored side by side and labelled; where they disagree the product says so instead of choosing for you.
**5d. "strong" in vv. 68/89** — **DECISION:** not yours to define from memory: one read-only corpus job (the classical-text search) checks whether the Muhūrta Cintāmaṇi ṭīkā itself defines strength in these verses; if it does, encode it as a `tika` reading; if not, the rules stay `strength_undefined` (honest "not assessable"). **Owner line:** we look in the text first; you are asked only if the text is silent.
**5e. Sarva-doṣa reach** — **DECISION:** stays inside the marriage chapter's own list (answer 01). Closed. **5f. Karakatva reach (OD-6)** — **DECISION:** the eight classes plus the father-bereavement Sun stay the rule (source-backed); widening is an addition if ever wanted. Closed. **Owner line:** both kept narrow and source-backed; reopen only if you want them wider.

### 6. PR #3402 (K6-5): holds lifted
**DECISION** — No action tonight; the v3 dispatcher handles it when the gate opens: the shared inheritance predicate first (verdict ACCEPTED at 298ddf15b, head now 60900206); if not inherited, VERIFY at the current head; if its generated census JSON is DIRTY against main, REGEN (never hand-merged); then the MERGE intent parks under HOLD_MERGES. Under WAIT it does nothing.
**Not delegable** — the merge itself.
**Owner line** — #3402 will be re-checked by the new fleet and then wait for your merge; nothing is needed from you now.

### 7. The working-copy ceiling (≈ 37 copies under `W`, limit 15; kalayantra holds 5)
**DECISION** — Enforce the owner's own policy on copies that cannot hold work: the cockpit removes every copy under `W` that is (a) clean (`git status --porcelain` empty), (b) whose HEAD is on `origin/main` or on a pushed branch (`merge-base --is-ancestor` or `ls-remote` match), (c) not written to in the last 6 hours, and (d) not on a `suvarna/*` branch and not `campaign-coordination` (a running loop works from it) — today that is the `detached-*` copies, `census-run-rev30`, `surface-run`, `review-3333b`, `review-es1b`, `k3-main`, `k3-pr`, `sweep-seals`, `tsc_final_f59cd1233`, and `audit-token-economy` if #3439 is merged; `review-3442` and `vocab-exec-pack` are dirty and stay. Suvarṇa's copies are theirs: one coordination line to madhav-04 asking it to release its finished copies within 24 hours per the policy (their share is 7).
**Cockpit now** — per copy: the three checks, then `git -C M worktree remove <path>`; `git -C M worktree prune`; report the count before and after.
**Not delegable** — Suvarṇa's copies (their work).
**Owner line** — the clean, already-uploaded leftovers of finished work are removed; Suvarṇa is asked to clear its own; you decide nothing.

### 8. The production switches and the rebuild (K-REBUILD-1)
**DECISION** — Go/no-go is mine by your record (`owner_authorisation_production_rebuild_20261013`): **no-go now.** Condition 3 (a verified backup through the installed executor) cannot be met: the backup and rebuild operations in the v3 table are unwired placeholders (`backup_snapshot`, `backup_restore_verify`, `orchestrator_rebuild[_dryrun]`: `TO_BE_SET_BY_J-1a/K9-3`, `enabled: false`). Sequence: J-1a and K9-3 build and dry-run them → you enable them (the switch) → the surrogate re-checks all five conditions → run. The two switches (starting the executor; enabling production operations) stay yours: both are production.
**Cockpit now** — J-1a and K9-3 go into the Wave-0 order of work right after the live item and the inbox triage.
**Owner line** — the production rebuild waits for its backup tool to exist; when it does you will be asked for two switches, not for a decision.

### 9. Backlog priorities created tonight
**DECISION** — Order: (1) inbox triage before any gate opening — the 57–58 unread inbox messages each become a RULING model launch the moment the gate opens: the cockpit dispositions them now (answered / obsolete / genuinely needs a ruling) and queues only the last class, one at a time; (2) the Wave-0 fix bundle as ONE bootstrap packet: `kyd_jobs` quarantines foreign-schema job folders instead of raising, the installer's legacy adoption writes a readable record, the installer qualifies the job-role templates, the "everything listed" test widened, `test_kyreconcile` staged-actions test updated, job PATH for docker-needing tests; (3) J-1a / K9-3 (production operation scripts, dry-run); (4) the fixture hand-off and KV3-B-FIXTURE-MODEL-JOBS — last; after the first real campaign items, not before.
**Owner line** — practice mode for model jobs is last on the list; the fixes that keep the fleet honest and the production tools come first.

### 10. Everything else found waiting
- **The first live item's PR (KV3-B-OPS-CONTRACT)** — merge or close is yours (merge). **Owner line:** one PR from the fleet's first run awaits your merge.
- **K8-R26** — needs an independent ACCEPTED verdict at 86cb61a2; a VERIFY the dispatcher raises once the gate opens; nothing from you.
- **K0a-3a** — an orphan id in the log; ignored by ruling. **K-AVADHI-C, K-NAK** — campaign items, no owner input.
- **Wave 0 start (D-7)** — when `READY_TO_START` holds, the surrogate proposes the resume record and you say yes or no; not today.
- **Morning-list 14/15/16** — Wave-0 tidy-ups, in the bundle of item 9.

**WAITS FOR THE OWNER (the complete list)** — (4) the executor restart, one line; (8) the two production switches when the tools exist; the merge of #3402 and of the first live item's PR when they are accepted; (D-7) the Wave-0 start when READY_TO_START holds. Nothing else.
