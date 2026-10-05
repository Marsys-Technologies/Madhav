# ARGALA_DIFF: L2 argala edges today vs what L1's argala_graha_natal facts say (chart 482012f1, read-only, 2026-10-05)

Method (all read-only; scripts in `scripts/argala_diff.py`, data snapshots in `data/`):
1. OLD = the argala computation of `bo_karanajala.py` at origin/main 56edf5d5a (`_build_argala_edges`: ARGALA_POSITIONS {2,4,11}, pairing 2-12 / 4-3 / 11-10, forward count for every graha, malefic-only cancellation, any occupant at the virodha position cancels), re-run as a pure function on the chart's L1 `graha_sign_attributes/sign_num` facts for each of the 5 ayanamshas.
2. PRODUCTION = the 119 `bodha_cgm_edges` rows with edge_type='argala' (build e22c92ca, computed 2026-09-11) mapped to graha names through `bodha_cgm_nodes`.
3. NEW = the 156 `chart_facts` rows of category `argala_graha_natal` (L1, N-61: offsets 2/4/5/11 paired 12/10/9/3, a node as the target counts in reverse). The new edge for a row is: from = source graha, to = target graha, relationship_class = argala_virodha if source in L2's (unchanged) MALEFIC set else argala_positive, cancelled_flag = (source malefic AND the row lists any obstructing graha), cancelling grahas = the row's obstructor_grahas.

BASELINE CHECK: OLD (pure re-run) == PRODUCTION on all 119 edges (offset, class, cancelled flag): 0 mismatches. So the table below is old production vs new, not old code vs a stale build. (The 10 cancelled production rows carry `cancelled_by_jsonb` NULL because that payload was added to the code on 2026-09-16, after the 2026-09-11 build; the re-run produces the payload; a rebuild writes it.)

## Totals

| | OLD (= production) | NEW (L1 facts) |
|---|---|---|
| argala edges, canonical chart (5 ayanamshas) | 119 | 156 |
| relationship_class argala_virodha / argala_positive | 44 / 75 | 64 / 92 |
| cancelled_flag = true | 10 (2 per ayanamsha) | **32** (7,7,7,4,7 for lahiri, raman, krishnamurti, surya_siddhanta, true_chitra) |
| uncancelled argala edges per ayanamsha (what Kala's `cancelled_flag = FALSE` filter admits) | 22 (21 for surya_siddhanta) | **25** (24 for surya_siddhanta) |

Edge-by-edge classification (per (source B, target A) pair, all 5 ayanamshas): SAME 74, CHANGES 30, APPEARS 52, DISAPPEARS 15 (old 119 = 74 + 30 + 15; new 156 = 74 + 30 + 52).

| class of difference | edges | why |
|---|---|---|
| APPEARS, offset 5 (extended) | 28 (18 on grahas, 10 on a node as target) | L1 lists the 5th (paired 9th); SS N-59 Q-L2-21 A-1: L2 follows L1, no separate BPHS {2,4,11} class |
| APPEARS, offset 2/4/11 with a node (Rahu/Ketu) as target | 24 (offset 2: 10, offset 11: 10, offset 4: 4) | L1 counts a node's argala in REVERSE (AR-2) |
| DISAPPEARS, node as target | 15 | old L2 counted forward from Rahu/Ketu; under L1's reverse count the same graha is no longer in an argala sign of the node |
| CHANGES: cancelled false -> true | 20 (16 with obstructor Moon in the 3rd = the 11-3 pairing, 4 with Ketu in the 10th = 4-10 pairing) | corrected pairing: old L2 took the 10th as the obstructor of the 11th and the 3rd of the 4th |
| CHANGES: cancelled true -> false | 8 | the old 11-10 pairing: Mars and Saturn in the 10th used to cancel Ketu's 11th argala; under the 11-3 pairing the 3rd holds no occupant in 4 ayanamshas |
| CHANGES: cancelling grahas differ (still cancelled) | 2 | surya_siddhanta: Mars+Saturn (10th) -> Moon (3rd) |
| class (positive/virodha) changes on a surviving pair | 0 | class depends only on the source graha |

Observable-output deltas on every edge (not only the pairs above): `constituent_fact_ids_array` was `[]` and is now `[the L1 fact_id]` (this is the point of the PR); `citation_human` gains " (counted in reverse)" on node-target edges; `edge_properties_jsonb` keeps the same four keys; `computed_strength`, `valence`, columns, constraints unchanged.

CONSEQUENCE FOR KALA (needs an owner decision, not hidden): `ka_kshetra/stage2_promise.py:330-340` reads only `cancelled_flag = FALSE` argala edges. The unchanged flag semantics applied to L1's corrected rows move the cancelled set from 10 to 32 and the admitted (uncancelled) set from 22 to 25 per ayanamsha (21 to 24 for surya_siddhanta); the identity of the admitted edges also changes (offset-5 edges, node-target reversals). This is a data effect of the L1 N-61 correction, not a TI-L2-37 flag-semantics change. S-L2 rebuilds bo_karanajala, so this reaches the Kala input at the S-L2 window unless the owner decides otherwise.

NOTHING THE L1 FACTS CANNOT EXPRESS was found: every field L2 writes today (offset, obstructing grahas, the paired virodha offset for `cancelling_roots`, direction) is in the L1 row; benefic/malefic is NOT stored by L1 ("one L0 definition, read by L2") so L2 keeps its own local MALEFIC_GRAHAS exactly as before (class and the malefic-only cancellation rule are unchanged). L1's `vipareeta_condition` (three or more natural malefics in the 3rd) occurs 0 times in this chart; L2 does not read it, so cancellation stays "any obstructor" (unchanged semantics); if a later chart has such a row, TI-L2-37 owns what to do with it.

## Pairs that differ (97 of 171 pairs; SAME pairs omitted), per ayanamsha

| aya | karaka B -> subject A | old | new (L1 fact) | difference |
|---|---|---|---|---|
| krishnamurti | Jupiter -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| krishnamurti | Ketu -> Mercury | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=6cf4b561dd1c292e | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| krishnamurti | Ketu -> Sun | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=a743da1fb9390506 | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| krishnamurti | Mars -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=b7e8a5cb7af7280a | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| krishnamurti | Mars -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=c996a8cb57dcf0a9 | APPEARS (offset 2, basic, reverse) |
| krishnamurti | Mars -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=f5bf3ec2ae93eaca | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| krishnamurti | Mercury -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=832cf1f92853668f | APPEARS (offset 11, basic, reverse) |
| krishnamurti | Mercury -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=6d881c3f9f847598 | APPEARS (offset 5, extended, reverse) |
| krishnamurti | Moon -> Ketu | off 4 argala_positive | - | DISAPPEARS |
| krishnamurti | Moon -> Mars | - | off 5 extended obstr=[] outcome=unobstructed fact_id=dcfff0f5b682ea1c | APPEARS (offset 5, extended) |
| krishnamurti | Moon -> Rahu | - | off 4 basic obstr=[] outcome=unobstructed fact_id=03d0f92cd7e2d222 | APPEARS (offset 4, basic, reverse) |
| krishnamurti | Moon -> Saturn | - | off 5 extended obstr=[] outcome=unobstructed fact_id=8754de36bf746730 | APPEARS (offset 5, extended) |
| krishnamurti | Rahu -> Mercury | - | off 5 extended obstr=[] outcome=unobstructed fact_id=ae10654a637a9169 | APPEARS (offset 5, extended) |
| krishnamurti | Rahu -> Moon | off 4 argala_virodha | off 4 basic obstr=['Ketu'] outcome=undetermined fact_id=06d34013bbd8ee20 | CHANGES: cancelled False->True; cancelling []->['Ketu'] |
| krishnamurti | Rahu -> Sun | - | off 5 extended obstr=[] outcome=unobstructed fact_id=f6a964dc09152317 | APPEARS (offset 5, extended) |
| krishnamurti | Saturn -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=7b8bc578e821eef3 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| krishnamurti | Saturn -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=8655d80065fbc0e1 | APPEARS (offset 2, basic, reverse) |
| krishnamurti | Saturn -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=9b85463ff8c22c64 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| krishnamurti | Sun -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=d8524425d1513bdb | APPEARS (offset 11, basic, reverse) |
| krishnamurti | Sun -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=262d4604ac81b912 | APPEARS (offset 5, extended, reverse) |
| krishnamurti | Venus -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| lahiri_chitrapaksha | Jupiter -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| lahiri_chitrapaksha | Ketu -> Mercury | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=f96d036b78303863 | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| lahiri_chitrapaksha | Ketu -> Sun | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=870e4f935a12ebe9 | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| lahiri_chitrapaksha | Mars -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=62966554e3639a39 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| lahiri_chitrapaksha | Mars -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=29be13aa42bf1084 | APPEARS (offset 2, basic, reverse) |
| lahiri_chitrapaksha | Mars -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=e61e3d3ef8cd9cb1 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| lahiri_chitrapaksha | Mercury -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=9208246d7e06097f | APPEARS (offset 11, basic, reverse) |
| lahiri_chitrapaksha | Mercury -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=7113b3d633c915e3 | APPEARS (offset 5, extended, reverse) |
| lahiri_chitrapaksha | Moon -> Ketu | off 4 argala_positive | - | DISAPPEARS |
| lahiri_chitrapaksha | Moon -> Mars | - | off 5 extended obstr=[] outcome=unobstructed fact_id=f4d85e08feb1e690 | APPEARS (offset 5, extended) |
| lahiri_chitrapaksha | Moon -> Rahu | - | off 4 basic obstr=[] outcome=unobstructed fact_id=7289dd3bf826c8de | APPEARS (offset 4, basic, reverse) |
| lahiri_chitrapaksha | Moon -> Saturn | - | off 5 extended obstr=[] outcome=unobstructed fact_id=d5094eb1ffa72232 | APPEARS (offset 5, extended) |
| lahiri_chitrapaksha | Rahu -> Mercury | - | off 5 extended obstr=[] outcome=unobstructed fact_id=105dd94dc3d88de9 | APPEARS (offset 5, extended) |
| lahiri_chitrapaksha | Rahu -> Moon | off 4 argala_virodha | off 4 basic obstr=['Ketu'] outcome=undetermined fact_id=7a64acff6d40b5c5 | CHANGES: cancelled False->True; cancelling []->['Ketu'] |
| lahiri_chitrapaksha | Rahu -> Sun | - | off 5 extended obstr=[] outcome=unobstructed fact_id=929a403b6f7da0b6 | APPEARS (offset 5, extended) |
| lahiri_chitrapaksha | Saturn -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=ff0d7d1f0955f4df | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| lahiri_chitrapaksha | Saturn -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=fa811c7bc3ee60c6 | APPEARS (offset 2, basic, reverse) |
| lahiri_chitrapaksha | Saturn -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=767a87ebf723035a | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| lahiri_chitrapaksha | Sun -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=fa243fba57a41301 | APPEARS (offset 11, basic, reverse) |
| lahiri_chitrapaksha | Sun -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=f09e8b7cb24b6e91 | APPEARS (offset 5, extended, reverse) |
| lahiri_chitrapaksha | Venus -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| raman | Jupiter -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| raman | Ketu -> Mercury | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=577916824a2cd70b | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| raman | Ketu -> Sun | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=8f080bcc2d7e25ed | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| raman | Mars -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=6a9318850656ad3c | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| raman | Mars -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=b14bc71f0f8e5117 | APPEARS (offset 2, basic, reverse) |
| raman | Mars -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=02a785cd3b5caa22 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| raman | Mercury -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=ab0f73f8b3061fd5 | APPEARS (offset 11, basic, reverse) |
| raman | Mercury -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=d5f5065b349b0f1a | APPEARS (offset 5, extended, reverse) |
| raman | Moon -> Ketu | off 4 argala_positive | - | DISAPPEARS |
| raman | Moon -> Mars | - | off 5 extended obstr=[] outcome=unobstructed fact_id=58e4e96dfea2fc42 | APPEARS (offset 5, extended) |
| raman | Moon -> Rahu | - | off 4 basic obstr=[] outcome=unobstructed fact_id=b844b825bf51d572 | APPEARS (offset 4, basic, reverse) |
| raman | Moon -> Saturn | - | off 5 extended obstr=[] outcome=unobstructed fact_id=633789eaeee3eb77 | APPEARS (offset 5, extended) |
| raman | Rahu -> Mercury | - | off 5 extended obstr=[] outcome=unobstructed fact_id=0ddb1ec95ed6a5a5 | APPEARS (offset 5, extended) |
| raman | Rahu -> Moon | off 4 argala_virodha | off 4 basic obstr=['Ketu'] outcome=undetermined fact_id=31bc1570208264a8 | CHANGES: cancelled False->True; cancelling []->['Ketu'] |
| raman | Rahu -> Sun | - | off 5 extended obstr=[] outcome=unobstructed fact_id=8052fdb33e888a87 | APPEARS (offset 5, extended) |
| raman | Saturn -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=fb2762005b989316 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| raman | Saturn -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=8794af45b5ce33ac | APPEARS (offset 2, basic, reverse) |
| raman | Saturn -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=3cc32475bb58e96e | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| raman | Sun -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=cacf1548f64d8f34 | APPEARS (offset 11, basic, reverse) |
| raman | Sun -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=995a37390f565499 | APPEARS (offset 5, extended, reverse) |
| raman | Venus -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| surya_siddhanta_classical | Jupiter -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| surya_siddhanta_classical | Ketu -> Mercury | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=['Moon'] outcome=undetermined fact_id=0e7b18eb0ebb0947 | CHANGES: cancelling ['Mars', 'Saturn']->['Moon'] |
| surya_siddhanta_classical | Ketu -> Sun | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=['Moon'] outcome=undetermined fact_id=35c93415de2247cb | CHANGES: cancelling ['Mars', 'Saturn']->['Moon'] |
| surya_siddhanta_classical | Mars -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=cbe3bae1087f6a7c | APPEARS (offset 2, basic, reverse) |
| surya_siddhanta_classical | Mercury -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=0d4f97732320bc13 | APPEARS (offset 11, basic, reverse) |
| surya_siddhanta_classical | Mercury -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=ed40ae154492bbf3 | APPEARS (offset 5, extended, reverse) |
| surya_siddhanta_classical | Moon -> Rahu | off 11 argala_positive | - | DISAPPEARS |
| surya_siddhanta_classical | Rahu -> Mercury | - | off 5 extended obstr=[] outcome=unobstructed fact_id=d11aeafa91f75651 | APPEARS (offset 5, extended) |
| surya_siddhanta_classical | Rahu -> Sun | - | off 5 extended obstr=[] outcome=unobstructed fact_id=070b36cca8411010 | APPEARS (offset 5, extended) |
| surya_siddhanta_classical | Saturn -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=fa9068fc81955f5f | APPEARS (offset 2, basic, reverse) |
| surya_siddhanta_classical | Sun -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=958ae0dc4acd27f1 | APPEARS (offset 11, basic, reverse) |
| surya_siddhanta_classical | Sun -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=bfe6ed616617c2e6 | APPEARS (offset 5, extended, reverse) |
| surya_siddhanta_classical | Venus -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| true_chitra | Jupiter -> Ketu | off 2 argala_positive | - | DISAPPEARS |
| true_chitra | Ketu -> Mercury | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=3dca7cef83d090b3 | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| true_chitra | Ketu -> Sun | off 11 argala_virodha cancelled by ['Mars', 'Saturn'] | off 11 basic obstr=[] outcome=unobstructed fact_id=0b5c37d960c9ef2f | CHANGES: cancelled True->False; cancelling ['Mars', 'Saturn']->[] |
| true_chitra | Mars -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=73cf91b3109bcf9a | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| true_chitra | Mars -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=3dc997586537a23e | APPEARS (offset 2, basic, reverse) |
| true_chitra | Mars -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=1b26f590434490b1 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| true_chitra | Mercury -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=098ed9d01f22302b | APPEARS (offset 11, basic, reverse) |
| true_chitra | Mercury -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=63c9a4bb0fecc3dd | APPEARS (offset 5, extended, reverse) |
| true_chitra | Moon -> Ketu | off 4 argala_positive | - | DISAPPEARS |
| true_chitra | Moon -> Mars | - | off 5 extended obstr=[] outcome=unobstructed fact_id=e6b2382aad3883ab | APPEARS (offset 5, extended) |
| true_chitra | Moon -> Rahu | - | off 4 basic obstr=[] outcome=unobstructed fact_id=cf4118604a7f1ae8 | APPEARS (offset 4, basic, reverse) |
| true_chitra | Moon -> Saturn | - | off 5 extended obstr=[] outcome=unobstructed fact_id=148cb045b5a36096 | APPEARS (offset 5, extended) |
| true_chitra | Rahu -> Mercury | - | off 5 extended obstr=[] outcome=unobstructed fact_id=1543a39c152995f9 | APPEARS (offset 5, extended) |
| true_chitra | Rahu -> Moon | off 4 argala_virodha | off 4 basic obstr=['Ketu'] outcome=undetermined fact_id=583a1203751c55a0 | CHANGES: cancelled False->True; cancelling []->['Ketu'] |
| true_chitra | Rahu -> Sun | - | off 5 extended obstr=[] outcome=unobstructed fact_id=78df09b04a0a5225 | APPEARS (offset 5, extended) |
| true_chitra | Saturn -> Jupiter | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=06c194b7853f7aea | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| true_chitra | Saturn -> Ketu | - | off 2 basic obstr=['Jupiter', 'Venus'] outcome=undetermined fact_id=b1245ee20cdec65c | APPEARS (offset 2, basic, reverse) |
| true_chitra | Saturn -> Venus | off 11 argala_virodha | off 11 basic obstr=['Moon'] outcome=argala_prevails fact_id=02b718e493201921 | CHANGES: cancelled False->True; cancelling []->['Moon'] |
| true_chitra | Sun -> Ketu | - | off 11 basic obstr=[] outcome=unobstructed fact_id=a8be1ed15b40c77e | APPEARS (offset 11, basic, reverse) |
| true_chitra | Sun -> Rahu | - | off 5 extended obstr=[] outcome=unobstructed fact_id=60afcbdb8210d3a3 | APPEARS (offset 5, extended, reverse) |
| true_chitra | Venus -> Ketu | off 2 argala_positive | - | DISAPPEARS |
