---
artifact: AM25_RETROGRADE_LOOP_ROOT_IDENTITY_CANDIDATE
version: "1.0"
status: AMENDMENT CANDIDATE (not ruled) — a named pre-condition of NUMERICAL activation; NOT part of the all-NULL milestone
date: 2026-10-02
author: Stream B (Śāstra), steward M20261002T084648-f2c2 (LOW priority, after packet v1_11)
evidence_rule: "Spec/oracle statements are quoted by locator from the frozen v1.4 files. Every number in §3 was produced TODAY by the kernel's own `solve_episodes` (services/gochara_kernel/episodes.py) on the real ephemeris — pyswisseph 2.10.03, Lahiri sidereal, pinned files sepl_18.se1 (sha256 ca1393ce…) and semo_18.se1 (1ca07bd6…) — for a natal target read from the canonical chart's L1 facts (read-only). No classical content is used."
---

# Retrograde loops: what is a "root" when the numbers are switched on? (candidate AM-25)

## 0. The question
Stream A's real-sky certification found that for a retrograde loop the builder emits several point-contact episodes, some overlapping in time, while the geometry has fewer in-orb intervals than episodes. Under the all-NULL milestone this is harmless (support/admission compare the **union** of the episodes — correct). Once numbers are enabled the question is **evidence accounting**: `path.c = Σ over roots of the per-root max` — are the episodes distinct roots, aliases of one root, or exact events inside one contact?

## 1. What the frozen text says (v1.4; unchanged by any amendment so far)
- **§2.1 (amendment 2, R4-S01):** `root_id := contact_id` on transit-relation rows; `contribution(path, root, c) := max over the records of that path sharing root_id of record.c`; `path.c := Σ over roots of contribution`; "no other reduction … is permitted".
- **§6.1 contact identity (NK-2):** `contact_id = hash(physical_object_id, occurrence_ordinal)`, where the ordinal indexes the **crossings** (exact roots) of one physical tuple ordered by `t_exact`. "A retrograde re-crossing of one target is therefore occurrence 2 of one object — **one physical object, two contacts**." **O-RX-1** pins exactly this (Mars, three crossings ⇒ ordinals 1, 2, 3; a fourth appended on partition extension). So **in the frozen text one exact crossing = one contact = one root**.
- **§1.2 inv 3:** role aliases of one physical contact share one `contact_id` (aliases are *roles*, not crossings).
- **Kernel episode definition (`episodes.py`, WP2 case-01 pin):** "one episode per exact root; an in-orb interval holding roots r₁…rₙ is split at the interior exact roots — episode k spans `[max(entry, r_{k−1}), min(exit, r_{k+1})]`". **Adjacent episodes of one in-orb interval therefore overlap by construction** (each spans from the previous root to the next), and `dwell_days` is defined so that the overlap is not counted twice in *time* (dwell_k = t_out,k − max(t_in,k, t_out,k−1)).
- **Oracles:** none pins evidence accumulation across a retrograde loop. O-RX-1 pins identity of three crossings; O-SS-2 pins boundary roots; O-SM-1/-3 pin station solving. (A search of the 57 oracles for shared-root / per-root / root_id accumulation found no loop case.)

## 2. Consequence: the frozen text double-counts one continuous stay
Because each crossing is a root and `path.c` sums over roots, **one continuous in-orb stay that contains k exact crossings contributes k times** — although the geometry is one approach, one continuous dwell. The overlap of the episodes is not an artefact: it is the kernel's pinned shape. So the three-episode / two-overlap picture is **by the frozen design**, and the accounting question is a real defect of §2.1 once numbers exist, not a builder bug.

## 3. The real loop (computed today; reproducible)
Target: canonical chart `482012f1…`, L1 fact `KET_MEAN / longitude_sidereal` = **229.0330°**. Body: Saturn, relation `drishti_contact` (Saturn's 10th aspect, 270° ⇒ Saturn at level 229.0330 − 270 = **319.033°**), orb 1.0° (`orb_drishti_slow`). Horizon 2023-10-01 … 2025-03-01 (UTC).

| episode | t_in | t_exact (root) | t_out | branch | dwell (d) |
|---|---|---|---|---|---|
| 1 | 2024-03-20 03:26:48 | 2024-03-28 17:27:07 | 2024-04-06 15:55:52 | direct | 17.520 |
| 2 | 2024-10-02 21:09:15 | 2024-10-21 09:21:57 | 2024-12-10 13:13:16 | retrograde | 68.669 |
| 3 | 2024-10-21 09:21:57 | 2024-12-10 13:13:16 | 2024-12-28 02:13:42 | direct | 17.542 |

**Reading it.** Three roots, **two in-orb stays**: stay A = episode 1 alone (Saturn passes the level once, leaves the band); stay B = `[2024-10-02 21:09 … 2024-12-28 02:13]` (87.2 d) — Saturn re-enters the band on its way back, **crosses the level twice** (the retrograde leg on 10-21, the direct leg on 12-10, turning at its direct station between them, inside the band) and leaves. Episodes 2 and 3 **overlap for 50.2 days** (`[2024-10-21 09:21, 2024-12-10 13:13]`) — one stay, two roots. With a wider orb the same structure becomes literally "one stay, three exact hits": at orb 7.0° (a stress value, not a proposal) the output is one stay `2024-01-30 … 2025-02-25` holding the three roots 2024-03-28, 2024-10-21, 2024-12-10, as three overlapping episodes. **Which shape occurs depends on the (still open, ND-ORB-ADMISSION) orb versus the loop's half-amplitude.**
(Disclosure on the steward's wording: in this real case at the 1.0° orb the three roots lie in two stays, not one. The rule below covers both shapes.)

## 4. Proposed rule (candidate AM-25 — for the native/Codex to rule; I do not apply it)
Keep **identity** exactly as frozen (NK-2, O-RX-1, ordinals, `contact_id`) and keep the **episodes** exactly as pinned (WP2). Change only the **accumulation key**:
1. **Stay.** A *stay* is a maximal connected in-orb interval of one (physical object, effective level). Its roots (0…n) are ordered by `t_exact`. `stay_id := hash(physical_object_id, occurrence_ordinal of the stay's FIRST root)`; a stay with no exact root (E8-2 tangency) takes `stay_id := hash(physical_object_id, "no_root", t_in at full precision)`.
2. **Accumulation (replaces `root_id := contact_id` in §2.1 only, for transit-relation rows):** `root_key := stay_id`; `contribution(path, stay, c) := max over the records of that path sharing stay_id of record.c`; `path.c := Σ over stays`. (Natal-fact rows keep `root_id := object_id`.) **One in-orb stay = one root; exact hits are sub-events of it** — they may carry timing (peak instant, solver stamps) but never multiply evidence.
3. **Unchanged:** `contact_id`, occurrence ordinals, the overlapping episodes, `dwell_days`, support/admission (union of episodes), geometry, every existing oracle. No score field changes under the all-NULL policy.
4. **When it takes effect:** with numerical activation (`window_qualification/1`). It needs a nullable `stay_id` column on `ka_gochara_relationship_record` (the 1233 pattern) and an independent verifier derivation (stays from the in-orb intervals, not from stored episodes) — a later migration, not 1240/1241/1242.
**Alternatives considered and rejected:** (B) keep one root per crossing and *divide* by the number of overlapping episodes or weight by dwell share — invents a weight no served text gives (CLAUDE.md B.10); (C) keep one root per crossing but forbid more than one root per record — leaves the overlap in admitted supports and does not fix the count; (D) merge episodes in the builder — rewrites the WP2-pinned episode shape and the O-RX-1 identity.

## 5. Oracle built from the real loop — O-RL-1 (proposed; executable at A5.5-numeric)
- **given (literals):** body Saturn; relation `drishti_contact`, aspect 270°; natal target `KET_MEAN` 229.0330° (canonical chart `482012f1…`, L1 `longitude_sidereal`) ⇒ level 319.033°; orb 1.0° (`orb_drishti_slow`); Lahiri sidereal, pyswisseph 2.10.03 on the pinned files (sepl_18 `ca1393ce…`, semo_18 `1ca07bd6…`); horizon 2023-10-01 00:00Z … 2025-03-01 00:00Z; daily knots; 1-arcsecond root tolerance.
- **then (geometry):** exactly 3 roots at `2024-03-28 17:27:07`, `2024-10-21 09:21:57`, `2024-12-10 13:13:16` UTC; exactly 2 stays: A `[2024-03-20 03:26:48, 2024-04-06 15:55:52]`, B `[2024-10-02 21:09:15, 2024-12-28 02:13:42]`; exactly 3 episodes as in §3; episodes 2 and 3 overlap on `[2024-10-21 09:21:57, 2024-12-10 13:13:16]`.
- **then (accounting, under AM-25):** with a unit record value c = 1 on every episode's record, `path.c = 2.0` (stays A and B), **not 3.0** (the frozen §2.1 sum over roots); stay B's `contribution` is the max over the records of episodes 2 and 3, and equals the larger of the two values (if c₂ = 0.6, c₃ = 0.9 ⇒ contribution 0.9; frozen §2.1 would give 0.6 + 0.9 = 1.5 for stay B).
- **mutation that must fail:** an implementation that sums over contacts (3.0 / 1.5), or that merges stays A and B (1.0), or that drops episode 3's record.
- **tolerance:** instants δt ≤ 30 min (the declared 1-arcsecond root tolerance at Saturn's ≈ 0.05°/day near its stations); stay edges δt ≤ 30 min; counts exact.
- **reproduce:** `python3 /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/am25_loop_probe.py Saturn 2023 2026` prints the §3 table (read-only; no database write).

## 6. What is NOT claimed
No doctrine about retrograde Saturn; no orb value; no peak or score is asserted — only the **count of independent evidence units** one stay contributes. The proposal changes nothing in the all-NULL candidate.
