# S-L1 window runbook v1.3.1 — ADDENDUM D (two explicit W7 chart_dashas read-backs for Pravāha's re-pin)

Status: addendum only; runbook v1.3.1 (sha256 783536b4ab7289bf06cec65f1766003e0ec4ec2f42d83471d0db55dc0b808131) stays locked. Directed by Strategic Suvarṇa (madhav-06). Pravāha's re-pin tool defines its checks on `public.chart_dashas` itself; either read-back failing = it would stop their re-pin, so either failing at W7 = ABORT (stop, tell SS and Pravāha, no workaround).

Run at W7 (after the last `ga_*` rebuild finished, with the W7.11 read-backs), reader, canonical chart `482012f1-710e-4a25-994a-93821f5871aa`, saved under `$EV/W7/ADDENDUM_D_*.txt`.

## D.1 (Q1) exactly ONE build id in chart_dashas, the new ga_dashas build
```
SELECT DISTINCT build_id FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
SELECT r.id, a.state, a.disposition FROM build_runs r JOIN build_run_assets a ON a.run_id=r.id WHERE r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND a.asset_id='ga_dashas' ORDER BY r.created_at DESC LIMIT 1;
```
Over the WHOLE table (every system and ayanamsha, including the `scope_cap` row and `mudda`): exactly ONE distinct build id, equal to the new ga_dashas run (complete / build). The old build `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb` must not remain; nothing is updated in place keeping an old build id. ABORT if two or more ids, or the one id is not the new ga_dashas run.
Rehearsal 2 evidence: one vimshottari build 0ffb87e2-… for all five ayanamshas, T4 stale survivors in chart_dashas = 0.

## D.2 (Q2) distinct (system_id, ayanamsha_id) pairs: 45 and 1
```
SELECT count(*) FROM (SELECT DISTINCT system_id, ayanamsha_id FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id <> 'scope_cap') s;        -- expect 45
SELECT count(*) FROM (SELECT DISTINCT system_id, ayanamsha_id FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'scope_cap') s;         -- expect 1 (scope_cap | INVARIANT)
```
45 = 9 systems (ashtottari, chara_karaka, kalachakra, mudda, naisargika, narayana, vimshottari, vimshottari_kp, yogini) x 5 ayanamshas; the `vimshottari_kp` rows keep `system_id = 'vimshottari_kp'`. ABORT if either count differs.
Rehearsal 2 evidence: snapshot_post.json.gz carries 9 systems x 5 ayanamshas = 45 pairs (the snapshot omits scope_cap by design); the post tier census (H25) carries `scope_cap|INVARIANT|4|scope_cap_sentinel|1` = 1 row, 1 pair; production before: `scope_cap|INVARIANT|4|1`.

## D.3 Also recorded for the SETTLED-1 values (read-only)
Tiers in the rehearsal post census: `vimshottari` levels 1-4 `two_pass_verified`; `vimshottari_kp` levels 2-3 `single`; vimshottari L1-3 row counts equal to the baseline; only level-4 counts move (before -> rehearsal after: krishnamurti 8155 -> 8156, lahiri_chitrapaksha 8165 -> 8177, raman 8043 -> 8034, surya_siddhanta_classical 7983 -> 7977, true_chitra 8164 -> 8166) by the Moshier-to-.se1 shift. The tier census as a whole changes in 30 level-1 rows (other systems' tiers) and 9 level-4 rows: not a vimshottari change. The `ga_strength` `receipt_spec_retired` check and the new ga_dashas build id for the notice are taken at W7.
