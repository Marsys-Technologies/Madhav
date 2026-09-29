# Suvarṇa v1.4: internal review, pass 3 (final, before the independent review and N-1)

Read-only. Scope: plan set v1.4 under `00_ARCHITECTURE/briefs/suvarna/`, `plan_model.json`, `/Users/Dev/suvarna/run/DECISIONS.jsonl`,
the tracker code at `ff70244a9` (485 tests pass, re-run 2026-09-30), the live tracker (`/api/state`) and one Monitor run
(`--once --json`: overall `warn`, rc=1). One read-only DB query was run as the reader, through `dag_levels`.
Findings already accepted as pending native decisions are not re-reported: N-25, the chmod of the dbenv files, branch
protection, N-26, N-14.R236, the F-3 content, N-23 and G16/N-4. Where a finding below touches one of these, the
finding is about code or documents that stay wrong whichever way the decision goes.

---

## A · Pass-2 fixes verified

**What was checked.** All 11 BLOCKERs (S1–S7, C1–C4), all 38 MAJORs (S8–S24, C5–C25), and 13 of the 21 MINORs (S25–S30,
C26, C29, C33, C35, C36, C38, C40): 62 findings in total. All 21 CODE specs were checked against the code.

| | Verified | Not fixed or partial |
|---|---|---|
| Findings checked (62) | **56** | **6** |
| CODE specs (21) | **12** implemented as specified (1, 2, 3, 4, 5, 7, 9, 10, 13, 16, 19, 20) | **8** partial (6, 8, 11, 14, 15, 17, 18, 21) · **1** not implemented (12) |

The plan-model graph has no cycles, no dangling dependencies and no decision item without a decision id.

**Not fixed or partial (the 6 findings):**

1. **S1, CODE-12 not implemented.** `monitor.check_isolation` (monitor.py:694–709) always returns `warn`
   ("N-25 not implemented"). None of the spec's checks exist: expected user, dbenv mode 600 or unreadable,
   `.config/madhav-admin` and `.codex` unreadable, the decisions log not writable, settings hashes against
   `settings_baseline.json`. The tests lock this in (`test_isolation_always_warns_never_ok_never_block`). CODE-20's
   "`--check` is what the isolation check calls" is not wired either. CODE-11 is also partial: the spec asked
   `main_protected` to report the bypass actors, but the detail prints only the expected actor ("not independently
   verifiable"). See B1.
2. **S2, CODE-14 partial.** `decisions.py` restricts `--writer` to `strategic-suvarna` but deliberately omits the
   interactive-TTY and typed-id confirmation (docstring, lines 26–40). Any process can therefore append a `decided` line
   with `writer: strategic-suvarna`, and the CODE-13 `decision_writers` check cannot see it. See B6.
3. **C3, CODE-15 partial.** `check_builder_scope` returns **`ok`** ("no builder identity recorded yet") when
   `builder_identity.json` is absent. The spec said the check is **absent** in that case. Live effect: the tracker shows
   **E7.3 = done** with E7.2 still open. See B2.
4. **S10(b), CODE-6 partial.** `d_scorecard_pass` hashes the generator that the **scorecard itself names**
   (`data.get("generator")`, detectors.py:726). The plan model's pinned `"generator":
   "platform/scripts/governance/nikasha_scorecard.py"` is never read. See B7.
5. **S14 partial.** The tracker and Monitor now run from hq, as specified. But the PreToolUse hold-guard hook in
   `runtime/settings.template.json` runs
   `PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance … hold_guard`. That is Strategic's working
   tree, which ROLE_COMMON §5 (line 116) forbids ("never from /Users/Dev/madhav-suvarna-plan"). If the import fails, for
   example because the `suvarna` user cannot read that path under N-25, the hook exits non-2 and fails **open**.
6. **C22 / S1, CODE-21 partial.** The narrowed `Bash(git push origin suvarna/lane/*)` was added, but the broad
   `Bash(git push *)` was kept, so the narrowing has no effect. The psql allow uses double quotes
   (`bash -c "source … && psql *`), while every role document uses single quotes (ROLE_COMMON:85, ROLE_ANALYST:50,
   ROLE_BUILD_OPERATOR:95). Arch §2.4 says `suvarna-build` and `python3` are allowed; neither is in the template. See
   B5 and B11.

**Partial CODE items that are cosmetic or have no functional effect:**

- **CODE-8:** the docstring of the `elevated_assets()` proxy still says "(E4.1)".
- **CODE-17:** the `NIKASHA_ROOT` default is still `/Users/Dev/madhav-nikasha` (server.py:62), not hq as the spec and
  the `run_tracker.sh` comment say. The value it reads is still correct, because it reads `origin/…`. Separately, the
  live tracker supervisor (pid 38014) was started at 15:23, before CODE-17, so the running server has no `NIKASHA_REF`
  and reads `/Users/Dev/madhav-nikasha` HEAD. Launch item L.17 corrects this.
- **CODE-18:** `lane_launch` emits `item: <qid>`, which is not a plan-model id and has no `step`. That contradicts arch
  §12.1, and the event is ignored by the tracker.

---

## B · Remaining blockers

(1) = deadlock or never-completable · (2) = change outside the charter · (3) = done/PASS without a real detector ·
(4) = document vs code/document contradiction that breaks the first execution day

| # | Class | Where | Finding and evidence | Smallest fix |
|---|---|---|---|---|
| B1 | (1)(4) | `monitor.py:694–709`; plan_model L.16a (`monitor_check_ok: isolation`); runbook §2 steps 2a and 6; charter §13 ("FI-7 waits") | The `isolation` check can **never** read `ok`: it is hard-coded `warn` under both N-25 outcomes, including the declined/fallback path. So L.16a can never be done. The launch checklist cannot complete either: step 6 requires "exits 0, with every check ok" and step 2a is "done when step 6 shows `isolation` ok". Live Monitor today: overall `warn`, rc=1. | Implement CODE-12 as specified: stat/hash checks only, `ok` when all pass. At minimum, cover the fallback path: dbenv mode 600, settings hashes equal `settings_baseline.json`, and `runtime_settings --check`. Replace the "always warn" tests. |
| B2 | (3) | `monitor.py:748–749`; plan_model E7.3; live `/api/state` | `builder_scope` returns **`ok`** before provisioning, so **E7.3 reads done now** while E7.2 is open. That releases E5.3 ("after E7.3"; it must be tested against the real builder). J1 criterion 13 also stays vacuously green if E7.2 is closed by event without `builder_identity.json` being written (E7.2 is done-by-event). | When `builder_identity.json` is absent, return `warn` or omit the check (CODE-15 says "absent"). Give E7.2 an `evidence_recent` detector on `run/builder_identity.json`. |
| B3 | (1) | plan_model J1.R (`register_freeze_clean`); `detectors.py:872–891`; register at `origin/campaign/nikasha-test` | J1.R needs **every** BLOCKS_FREEZE row to be CLOSED or DONE. R34 and R36 are BLOCKS_FREEZE and `CLOSED_ON_BRANCH` (engine A1/A3, "pending merge / migration / deploy / runtime proof"; R34 also carries an OPEN residual). No plan item or detector owns closing them. Plan §4.2 row 6 lists only R24, R39, R71 and R244. J1.R therefore cannot go green, and J1.6's checklist cannot complete. | Add an item after E3.7 (for example E3.8, "R34 and R36 closed after deploy and runtime proof"; split R34's residual into its own non-freeze row) with `register_rows_closed`. Add R34 and R36 to J1.R's `expect_rows` and to J1 row 6. |
| B4 | (1)(4) | hq/main `.claude/settings.json` deny (from L3 Kāla #2718); arch §12.5; Track E E7.1 and E3; plan §8 N-26 | The committed project settings deny `Edit(platform/migrations/10[0-6][0-9]_*)`, `1070_*`, `11[2-9][0-9]_*` and `1[2-9][0-9][0-9]_*`. Main is at 1125, so every Suvarṇa migration needs 1126 or later and is **refused in every lane**; a deny beats the `--settings` allow. This hits E7.1's grant migration (available on day 1), N-26's renumbering, any Track I migration, and F-3 if Suvarṇa lands it. Only L3's reserved range 1071–1119 is writable, which contradicts §12.5 and the N-26 recommendation. | Native-approved change to the project deny: exempt Suvarṇa lanes or a Suvarṇa range. State the rule in §12.5 and in N-26's options. |
| B5 | (2) | `settings.template.json` allow `Bash(git push *)` (plus project `Bash(git push*)`); denies only `--force*`, `-f*`, `* main*` (plus project `--delete`, `origin :`) | Not denied: `git push origin +HEAD:<branch>` (a force push through a `+` refspec) and `git push origin HEAD:main` / `…:main` (`* main*` needs a space before `main`). So a swarm agent can force-push onto other workstreams' branches (`l3/*`, `campaign/*`, `strategy/suvarna-plan`, which carries the tracker code) and push directly to main. Only main is (to be) protected. | Drop the broad push allow. Deny `Bash(*git push*+*)` and `Bash(*git push*:main*)`. Have the hold-guard hook refuse any push whose destination is not `suvarna/*`, or the Engine fold fast-forward to `campaign/nikasha-test`. |
| B6 | (2)(3) | template allow `Bash(python3 -m suvarna_tracker.* *)`; `decisions.py` (CODE-14); `runtime_settings.py --template`; `census_lock.py` | The wildcard allows (a) `decide --state decided --writer strategic-suvarna` (a forged native ruling that the `decision_writers` check cannot detect); (b) `runtime_settings --write /Users/Dev/suvarna/config/claude-settings.json --template <lane file>`, which rewrites the swarm's own permissions (the `Edit` deny does not stop a subprocess); and (c) `census_lock --emit -- <any command>`, a wrapper that bypasses every Bash deny. These are independent of N-25: (c) still bypasses the deny list under a separate user. | Deny `Bash(python3 -m suvarna_tracker.decide*)`, `…decisions*` and `…runtime_settings*` in the template (Strategic runs outside it). Make `census_lock` refuse any command that is not the `asset_census.py` form. |
| B7 | (3) | `detectors.py:726–745`; plan_model E1.7 (J1 criterion 1) | The generator hash check trusts the generator path the scorecard itself names, so the spec's pin is dead. A committed JSON that names any committed file, with that file's sha256 and PASS verdicts, reads done. | Require `data["generator"] == spec["generator"]`, plus a test. |
| B8 | (3) | plan_model E4.2r (`register_rows_state`, no `deferred_withholding_entry`); J1.R `allow_deferred: [R244]` | R244 = DEFERRED counts on its own say-so. The plan's claim is "deferred **with withholding**", and the register says R244 "must be manually withheld from every emit". Without it, bo_upaya's unearned Idem PASS can reach a W2 certification before B.U. The code already supports this check (`_withholding_has_entry`), but the spec does not pin it. | Add `"deferred_withholding_entry": "bo_upaya-Idem.pattern"` (the E5.2 entry) to E4.2r. |
| B9 | (2) | arch §6.2.2 ("one orchestrator run covering that whole level"); Track E §7 E5.3 (dispatch via `suvarna-build`); plan §9 family levels | Family assets sit inside waves: `ka_gochara_resonance` and `ka_vedha_gochara` at level 1 (**W0**), `ka_gochara` at 5, `ka_kshetra` at 12, `ka_sangam` at 13; readers `mi_bhara` and `mi_sankalpa` at 13. A whole-level run rebuilds family data in production (charter R8, N-17). Only ROLE_BUILD_OPERATOR's prompt-level screen stops it, and the E5.3 script spec does not exclude them. | Arch §6.2.2 and the E5.3 spec should say: dispatch `--assets <level minus FAMILY_ASSETS.family_set>`, never `--level` for a level that holds a family or reader asset. The E5.3 test asserts this. |
| B10 | (4) | template allow list vs arch §2.4 and role documents | Applies if N-25 is decided yes (the recommendation). The `suvarna` user has no native `Bash(*)`, so on day 1: the analysts' documented single-quoted psql reads are refused (B11 below is the same mechanism); `python3 <script>.py` is refused (builders can run only `-m suvarna_tracker` or `pytest`); `~/.config/suvarna/bin/suvarna-build` and `pg_dump` are not allowed, so E5.7, E5.3 testing and all wave dispatch are refused. | Add `Bash(bash -c 'source ~/.config/suvarna/pgenv.sh && psql *)`, `…&& pg_dump *)`, `Bash(python3 platform/scripts/governance/*)` and `Bash(~/.config/suvarna/bin/suvarna-build *)`, or change the documents to the template's form. |

**B11** is folded into B10: it is the same allow-list mismatch.

**Below blocker, worth fixing before the independent review:**

- **F3.FK (`fk_no_cascade`)** reads done if the keys become RESTRICT or NO ACTION. Plan §9 says such a replacement
  "would refuse the L2 delete-then-insert", so the W0 MSR rebuild would fail (loudly). Treat `confdeltype` in
  (`c`, `r`, `a`) as pending.
- **E6.3t** is done by event, with no detector. The E6.3 interface is not pinned in Track E §8: the tracker calls
  `elevated_assets(cfg)` from `origin/main`, while the current module reads ledgers from its working tree. J1 can
  therefore pass with every wave detector reading unknown. Pin the interface and give E6.3t a detector that the
  loader returns non-None.
- **`levels_elevated`** takes wave membership from the live registry DAG, not the J1-frozen `LEVEL_MAP.json` that the
  plan names.
- **`wave_deployed`** trusts whatever PR number `evidence/<wave>/LANDING.json` names. It should check the PR's head
  ref is `suvarna/land/<wave>…`.
- **`main_protected`** reads done without checking bypass actors. The ruleset's `bypass_actors` can be read.

---

## Answers

1. **Deadlock or never-completable item: yes.**
   - L.16a: the isolation stub can never be `ok` (B1).
   - J1.R: R34 and R36 have no owner (B3).
   - Every Suvarṇa migration is denied by the committed project settings (B4). This blocks E7.1, and therefore
     E7.2, E3.7 and J1.
2. **Change outside the charter: yes.**
   - Force-push through a `+` refspec, and a push to `…:main` (B5).
   - Decision forgery and self-rewritten permissions through the `suvarna_tracker.*` wildcard, and the `census_lock`
     wrapper around every deny (B6).
   - Whole-level runs that rebuild family assets, starting in W0 (B9).
3. **Done or PASS without a real detector: yes.**
   - E7.3 is done now (B2).
   - The scorecard generator pin is ignored (B7).
   - R244 DEFERRED is accepted without its withholding (B8).
   - Near-blockers: F3.FK passes on a restricting key; `main_protected` does not check bypass.
4. **Documents contradicting code or each other on the first execution day: yes.**
   - Runbook steps 2a and 6 cannot be satisfied (B1).
   - E7.1's migration is denied (B4).
   - Under N-25 = yes, the documented psql, script, dump and build commands are refused by the template (B10).
   - The hold-guard hook runs from Strategic's worktree and fails open (A.5).
