---
artifact: ASTRA_REVIEW_TRAIN_STAGE2_SHAPE_B
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: ACCEPT_WITH_AMENDMENTS
authority: "Review only; authorizes nothing."
---

**MAY #2999 BE MERGED UNDER THIS RULING — YES, after correcting the rationale and satisfying the pre-merge conditions below.**

1. **The stated cause is incorrect.** Neither 1232, 1233, nor 1240 grants privileges on `ka_gochara_search_inventory_verification`. CI connects as `postgres`, but the Moon-domain suite switches to `data_plane_builder`; `moonBuild()` then calls `verify()`, which attempts an **INSERT** as that builder. Migration 1206 deliberately gives the builder no privileges on this table.

   #2999 fixes the test: `verify()` switches to `gochara_verifier`, and fixture setup explicitly grants that role the necessary privileges. **This suite does not apply 1240 at all.** The deterministic failure is a stale test-role setup exposed by #2919’s expanded CI step, corrected in #2999—not missing 1240 grants. See the [corrected helper](https://github.com/Marsys-Technologies/Madhav/blob/17115720c63261ae4f13f488b01f1af263acd1fb/platform/tests/integration/gochara_b6_am14_moon_domain.db.test.ts#L368-L379) and [fixture setup](https://github.com/Marsys-Technologies/Madhav/blob/17115720c63261ae4f13f488b01f1af263acd1fb/platform/tests/integration/gochara_b6_am14_moon_domain.db.test.ts#L482-L506).

2. **The corrected, one-stage exception is technically safe.** It waives a repeated refusal observation at the intermediate tree. The three safety guarantees remain: failed CI prevents routine migration/deployment execution; successful CI encounters the protected-file refusal; service jobs require successful migration. `deploy.yml` and `migrate.ts` are byte-identical between the supplied main and #2999 refs. The earlier shape A proves refusal; final-main shape A must prove it again before dispatch. A red base has no additional execution risk merely because it is red.

   Record the exception against the exact SHA/run and corrected failure mechanism. Require all six required checks **and the entire DB-integration job** to finish successfully on the exact #2999 head before queuing. “Running,” an earlier head’s success, or skipped failing suites is insufficient. Preserve builder/verifier separation.

3. **Condition (iii) is necessary and correct, but supplements the existing checklist.** Require fully green CI and completed shape A for the **actual final merged main SHA**, with the named 1204 refusal and all four deploy jobs skipped. Retain row 7’s final-tree selection test, ten hashes, trigger-manifest comparison, absence of 1241, ledger comparison, and row 8’s drained lane and other prerequisites. Any intervening main change requires requalification. Neither green disposable-DB tests nor this exception establishes production inventory ACL completion.

4. **Narrowing CI through another PR is worse during this freeze.** It removes exercised coverage, adds another merge/run and qualification cycle, and does not repair the test-role defect. Prefer the already-reviewed correction in #2999 under the recorded exception.

Source verification confirmed `17115720c` and `0acd0146b` have identical trees. Fetch was sandbox-blocked; local refs matched your supplied SHAs. Run outcomes and ledger state are supplied evidence, not independently live-verified here. No files written or production accessed.