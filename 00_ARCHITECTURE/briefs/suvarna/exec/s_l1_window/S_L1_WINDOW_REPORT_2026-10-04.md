# S-L1 WINDOW REPORT (runbook v1.3.1 W7.17) — chart 482012f1-710e-4a25-994a-93821f5871aa

Written by Exec Suvarṇa (madhav-b2), 2026-10-04. Runbook sha256 783536b4ab7289bf06cec65f1766003e0ec4ec2f42d83471d0db55dc0b808131; ADDENDA A 7d9cf709…a8cc, B 8e17bf55…18cc, C ed696b1e…26d1, D b22255a7…1d745, E 020e32ed…57f98. Evidence root `/Users/Dev/suvarna-evidence/S_L1/window/` (TIMELINE.tsv has every step). No birth inputs, credentials or private text in this file.

## 1. Authority and timeline (UTC)
- 02:08:23 W0 start (SS decision N-126: the 07:30Z slot cancelled, owner words relayed by SS). Backup (gate A6): Cloud SQL ON_DEMAND id 1791079716170 SUCCESSFUL (02:08:36–02:10:17).
- 02:08–02:42 W0.2–W0.15 and pre-arm checks; W0.4 closed once deploys 37169765973 and 37170513781 completed (tip f2526fe13).
- 02:41:56 #3122 armed; ejected ~02:55 (merge-group CI failed on test_disposable_pg_watchdog, a harness race); SS decision: re-queue once; re-armed 02:56:20; merged 03:08:19 as M1 5ff71f3419f697ddde8e9ede6a3f01187f1ba0da.
- 03:34:42–03:34:53 the seven migrations applied by deploy run 37173883106 (DEPLOY_SHA = M1). Pipeline job image NOT re-pointed (gate skipped: no pipeline source change): IMG_SHA a5b3b7b263a3a41873b939b6b29df28a2025073a (Addendum E, SS confirmed).
- 03:52:36–03:53:17 D6 dry run (EVD 11becc44…); 03:54:27–03:55:43 D6 apply, ACCESS EXCLUSIVE window 03:55:35.590–03:55:42.495 (6.9 s, 65 statements).
- 03:56:33 watchdog PAUSED (PAUSE_T); baseline of planned/running/paused runs EMPTY; cap 09:56:33.
- 03:57:17 T0 = ga_positions dispatch; run 15862437-7303-43aa-ae01-72be94a8c2fc, exec brahma-build-pipeline-job-hgngt, finished 03:59:13.
- 04:14:23 17-asset dispatch; run 75524b3e-102a-43ec-8cee-3f57fee752c3, exec brahma-build-pipeline-job-vn4w8; ended 06:04:41 (ga_vargas 04:16:38–04:25:00, ga_dashas 04:25:09–05:02:00, ga_structural 05:04:37–05:55:09, ga_vichara 06:00:44–06:04:22).
- 07:40:42 watchdog RESUMED by SS (audit log; SS says 07:40:48); verified ENABLED by Exec 07:54; tick observed 08:00:04. Pause 3 h 44 min (< 6 h cap).
- 07:52 Exec session resumed after a ~3 h 10 min suspension (cause unknown, likely a usage limit); SS polled in the meantime.
- 07:55 G-IDX; 07:57–08:11 W7 checks; closing STATUS sent to SS.

## 2. Step results (all PASS)
W0.1–W0.15 PASS; W0.14 BEFORE by SS (Addendum C.1); W1.1 (7 shas = Appendix B, unapplied set = exactly seven, number guard PASS); W1.3; W1.4 (seven ledger rows with the approved sha256); W1.4B (#2900, #2943, #2896, #2898, #2957, #2959 CLOSED, none merged); W1.5 (md5s ga_medical ae453edf…, ga_sensitive d6dc2925…, ga_structural c56f9e12…, ga_vargas d2f89753…; edges; specs 1|2; exactly six ga_* fresh→stale; ownership 236; builder SELECT t); W1.6 (Addendum E); W1.7 ROUTE_B PASS (config python 3.11.17, SE_EPHE_PATH=/app/ephe; .se1 pins; pyswisseph 2.10.3.2, pyjhora 4.8.6, numpy 2.4.6, scipy 1.17.1, psycopg 3.3.6, psycopg-binary 3.3.6, psycopg2-binary 2.9.13, timezonefinder 9.0.0; swisseph binary 3911614c…; source layers == worktree 865 files diff 0); W1.8 PASS; D6.1–D6.6 PASS (verify_after_apply 30 PASS + 2 INFO; function md5s 873ee5da…, 31d005e8…, b2f4242f…; seven-column unique index; trigger args 7 and 9); W2.5; W3.5; W3.6 (FORENSIC 47 passed=True + 10 assertion=none, 0 passed=False; 67 backend lines all swieph /app/ephe; 0 ERROR, 0 Traceback, 0 WRITER GAP); W3.7; W7.1–W7.16 and Addendum D (see TIMELINE.tsv and the files in W7/).

## 3. Key numbers
chart_facts 147,751; chart_divisionals 38,596; chart_dashas 483,855; chart_vichara 7,774; chart_fact_identity 133,832 (= parsed; gap 0; reason set exactly 15); one chart_dashas build 75524b3e-…; 45 + 1 (system, ayanamsha) pairs; flip detector 24 stems NOT_CHECKED exit 4 by design, 7 failure classes 0, changes 35,312 unattributed 0, expectations 76 True, anchors 7/7 (19 True); final run with --allow-not-checked exit 0. Per-system dasha shifts: vimshottari 6,991–6,993 s; kalachakra 145,089 / 145,110 / 150,309 s; mudda true_chitra −42 s. Level-4 vimshottari deltas: +12 / +2 / +1 / −9 / −6.
Id-map path: /Users/Dev/suvarna-evidence/FactId/W0_S_L1_20261004T021155Z (MAPS.sha256 inside). W0 baseline snapshot sha256 966e0e23f4d3da8072c6f17d93983b1d57a13d7394258e5dfc9062d356b718fa.

## 4. Problems found and how they were handled
1. Governance pins did not know the W1 migrations (first CI red, 3 real failures): two minimal non-SQL pin edits (1226 into registry_depends_on_migrations.json; 1221 into DERIVED_ONLY_MIGRATIONS), SS accepted.
2. Merge-queue ejection on an unrelated flaky test (test_disposable_pg_watchdog race): not rerun on my own; SS decided one re-queue; it passed. The flake itself should be fixed by the engine.
3. Pipeline job image not re-pointed by the W1 deploy (gate working as designed): Addendum E, two proofs (inventory 124 writers byte-identical; pipeline-path diff empty).
4. Pre-existing served outage: lagna frame unresolved for judgment_query / assess_* because ga_positions keeps a leftover `__whole_asset__` receipt partition in state unknown since 2026-09-07 (Addendum C). S-L1 did not repair it, as predicted from rehearsal 2. FIRST post-window item after the password rotation (PW.1b, orphan-receipts package #2910, T0 = 2026-10-04T03:57:17Z).
5. ACCESS EXCLUSIVE window was 6.9–8.8 s in production (65 statements, round trips through the proxy) vs 170 ms in the rehearsal: accepted by SS.
6. My first D6 pre-apply check script aborted itself (gh ran outside a git repo and could not count deploys); nothing was touched; fixed and re-run.
7. Slips of mine, all disclosed to SS: a mistyped BOUND hash in a status message (corrected); two wrong clock stamps in messages (corrected); my session was suspended 04:40–07:52Z so the 10-minute poll cadence was missed (SS covered it).
8. The watchdog was resumed by SS (shared production identity) before my W7.1; recorded as such.
9. FINDING (accepted by SS as dependency propagation, not rebuilt by design): ga_prashna asset_throughput lit → stale (dependency on the rebuilt ga_positions); its freshness row and data unchanged. It is an ADDITION to the declared stale set: 17 assets stale in asset_throughput (the 16 declared L2/L3 assets plus ga_prashna), not 16.
10. Snapshot dasha count 483,869 (label rows) vs raw 483,870 at W0: label-row collapse, equal to the rehearsal's flip report.

## 5. Open / next
SETTLED-1 issued by SS (~08:15Z) and the window CLOSED with RELEASE (merges and arming allowed again). Then PW.1 reader password rotation (owner-authorised, needs SETTLED-1), PW.1b orphan-receipts (#2910: merge main, recompute hash, SS approval, dry run with --min-build-after T0, apply), PW.2 migration 1256 (MV refresh), tests-only PR (first commit: #2898 seed edit + parity test + intent doc), then the rest of the post-window list. No corpus or calibration run until S-L2 closes.
