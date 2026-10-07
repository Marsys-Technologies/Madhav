**DECISION BY DELEGATE (second packet) — 2026-10-05**
Fable 5.1 for the owner under Ruling 12; read-only. Sources: RULING10/11/12, G10/G11 packets, ND-H-20261005, GRAZE list, frozen specs v1.4, BASELINE/PROTOCOL v2.3, sealed doctrine v3.0, origin/main `dcbf67e60` (`registry.py`, `evaluator.py`, `admission.py`, `permission.py`, `record_store.py`, `window_sweep.py`, `convention.py`), served corpus.

## A. Near-miss — meaning of "sandhi"

**DECISION.** R2 is the kind; a junction flag (hybrid) is carried as data, never as a filter.

**RULE.** Every certified near-miss (complete rootless stretch, positive clearance, per G11-reconciled) is stored and shown. Each carries `at_junction ⊆ {rasi, nakshatra, dasha}`: `rasi` iff a `sign_ingress` sky-event of the *transiting body* falls inside `[t_in, t_out)`; `nakshatra` iff a `nakshatra_ingress` of that body does; `dasha` iff an MD or AD boundary instant (§4.0 pinned read) does. Measured on the body's own motion — not the natal point, not the aspect ray. No tolerance number is introduced: the stretch is the band. The flag is a served facet and a diagnostic split; it admits nothing.

**BASIS.** Classical *sandhi* = rāśi/bhāva/daśā junction (gaṇḍānta: BPHS `bphs_pg0111_c01`, OCR-unverified, per `brahmagyan/gandanta.py`); my stated HIGH-text searches for bhāva-sandhi and daśā-sandhi clauses located nothing. No text links a station-near-a-natal-point to a sign cusp — R1 has no doctrinal mechanism. "Falls in the sandhi" read as "falls in the threshold zone without crossing" is accepted usage. Grade: R2 = owner's category + derivation; junction flag = classical meaning (locus only for gaṇḍānta).

**REASON.** The owner's clause "the dignity of that window that opens up" treats the whole kind as window-opening; R1 would keep ~2 (target-near-cusp) or ~6 (ray-level) of 24, defeating "opportunity loss". R2 honours the words and the product; the flag keeps R1 testable rather than dismissed.

**Changes.** G11-reconciled Q1 closed (R2 confirmed); add the flag spec to AM-G11.

## B. Near-miss — treatment

**DECISION.** Confirmed with four amendments.

**RULE.** (1) A *slow-agent* (Jupiter, Saturn, Rāhu, Ketu) near-miss opens its own `near_miss` window from day one, labelled, categorical standing below `contact`, visible where no contact window exists; a *fast-agent* near-miss (Sun, Mercury, Venus, Mars — 16 of the 24) is a refiner annotation inside any overlapping window of either standing, else listed `refiner_no_window` (consistency with E). (2) Near-miss supports never union with contact supports (no bridging), never enter P4 `infl()`, never form `eval_window` rows; `score` NULL with reason `near_miss_unscored`; `proximity = 1 − d_min/orb` and `at_junction` stored. (3) No numeric discount coefficient exists — "lower, not zero" is categorical standing plus separate serving (§N.6), not an invented weight (B.10). (4) Every endpoint computed with the layer present and absent must be byte-identical, including T-honesty.

**BASIS.** Phaladīpikā XXIII.13 (TOC `phaladeepika:PG31:C1`, HIGH; verse body unread): a planet transiting "the exact degree" of its natal place "reveals the full effects" — exactness is the full-effect condition, so non-exactness is honestly lower. Station intensity is accepted practice (UK quoted at `nadi_navamsa_patel:PG2516`, MEDIUM).

**REASON.** Astra P1-8 showed any scored extension can turn misses into hits, bridge candidates and create P4 intersections; amendments (2) close all three by construction. The owner's "not equal" is honoured as standing, which no later coefficient can silently inflate.

**Changes.** G11-reconciled Q2 closed; items 2–4 gain amendments (1)–(4).

## C. K-B for bereavement

**DECISION.** Uniform: natal Sun is a K-B target for bereavement; no carve-out.

**RULE.** Bereavement (father) gains `object_role karaka` degree-point edges on natal Sun for Jupiter/Saturn (conjunction, aspect) and Rāhu/Ketu (conjunction) in P3 and in P4 `infl()`, at the substrate's ratified contact band (ND-ORB; `ORB_TABLE orb_conj_slow = 1.0°` today) — never a K-B-specific orb (ND-H's "5°" is `admission.py`'s oracle constant, not the built band; AM-H must say which). Māraka testimony and H unchanged. Guard: ND-H condition 4's reversion mechanism applies (below).

**BASIS.** Sun = father's lagna: Phaladīpikā XV.22–24 (TOC PG23:C1, HIGH), BPHS 7.39–43 (PG102:C1, per ND-H); Sun kāraka of bereavement is already `verse_cited` (PhD II.1, `registry.py:176`). Saturn-over-natal-Sun → father's affliction: Nāḍī practice (`PG1164`, MEDIUM). The HIGH Saturn-transit relative rule (`bphs:PG880:C2`) is piṇḍa-based (P5d, held). Grade: derivation from HIGH frames + accepted practice.

**REASON.** The same mechanism (malefic transit over the father's lagna) serves illness and death; the difference lives in H, māraka and P1 — not in whether the Sun is a target; carving it out makes K-B class-dependent for no doctrinal reason, and an ācārya timing a father's death reads the Sun first. Budget honesty: bereavement's P3 is already geometrically saturated for a 4-house H (Astra: Jupiter 10/12, Saturn 11/12 bins); the 2.61 % budget is decided by P1/P4, where K-B is one more `infl()` route and is guarded.

**Changes.** ND-H "owner's own" item 1 closed; AM-H adds the orb clause.

## D. P1 prerequisite (2) — kāraka as period lord

**DECISION.** Kārakatva is a fourth relation kind satisfying prerequisite (2), scored by this ruling, MD/AD only.

**RULE.** Add to `P1_RELATION_KINDS`: `{relation: "karakatva", target: "class_karaka", provenance: "uncited_extension", operator_role: "scored", ruling_ref: <this ruling>}`. `period_lord_relation()` returns `karakatva/scored` when the level lord ∈ `KARAKA_SETS[class]` (cited rows or ND-H K-A rows), evaluated after occupancy/ownership, before dispositorship. PD stays testimony (ST-P1-PD). Nodes: licence recorded; no P1 transit content exists for nodes today, so no window effect. The licence changes nothing else in P1 — windows still form only from XX.34–38's residence content inside the anchor's periods.

**BASIS.** Spec §2.2 lists (2) as "natal bhāva relationship"; the B3.8d read found no non-node dispositor/association clause in XX.34–38, and none for kārakatva either — so it cannot be `verse_cited`. Kārakatva itself is `[D]` (PhD II.1–7; XV.15–17 TOC PG23); "a kāraka's daśā delivers its signification" was not located in HIGH texts by my searches — accepted practice.

**REASON.** Every practitioner reads Venus daśā for marriage and Jupiter daśā for children; refusing the licence loses that opportunity. Density is bounded: it adds (lord, class) pairs only where the lord is the class kāraka (one or two per class), and P1's admitted days remain gated by the lord's own/exaltation/debility residence (3–4 of 12 signs) inside its periods.

**Changes.** ND-H item 2 closed; `rule_version 1.2.0` P1 row; `evaluator.py` D3 note gains the kind; verifier table updated independently.

## E. P3 fast-agent density

**DECISION.** Option (ii), generalised to both union-over-agents transit paths: slow agents open, fast agents refine.

**RULE.** Agent tiers: slow = {Jupiter, Saturn, Rāhu, Ketu}; fast = {Sun, Mercury, Venus, Mars}; Moon unchanged (AM-4/P6). For P2 and P3 at `rule_version 1.2.0`, every fast-agent transit record carries one more necessary predicate `slow_support_overlap` (operator `overlaps`; operand = connected union of the same grain's admitted scored slow-agent supports), evaluated as `_p4_double_transit` is; false ⇒ `not_admitted`, reason `refiner_without_slow_support`. Window components = union of slow-agent admitted supports only; fast admitted records are members where they overlap and contribute to objective, peak and score, never to the interval. P1 untouched (daśā-gated; XX.38's Sun is a cited opener). P4 already slow-only. Near-miss windows obey the same rule (B.1).

**BASIS.** Accepted practice (slow transit gives the event, fast pinpoints the month: `nadi_navamsa_patel:PG2048`, MEDIUM); sealed doctrine v3.0 §2.1 L2 ("slow-body residence … as support"; "Sun's month where a rule uses it; Mars where a rule uses it") and §2.4 P3 row, which says **slow-body** — the frozen spec's §2.1/registry widened P3 to nine agents without a stated reason. BPHS ch.70 Sun-month `[D]` stays a rule-specific opener (P5e, held).

**REASON.** Arithmetic, not measurement: residence ∨ aspect on two houses puts Sun/Venus in contact ~4 of 12 months each, Mars ~4 of 12 positions, Mercury similar; their union alone covers roughly four-fifths of days — the 99.87 % mode rebuilt by geometry, before slow agents. P2 leaks worse (Venus favourable in 9 of 12 houses). This is a design amendment to the frozen P2/P3 predicate sets, but it restores the sealed doctrine rather than contradicting it, and it is not a "fixed planet→grain law": fast agents still act at their grain inside windows and P1's Sun still opens by its verse.

**Changes.** ND-H item 3 closed; ND-H condition 4's "P3 fast" report becomes "fast-refiner contribution"; AM-G (grain) in the v1_5 draft.

## PRE-REGISTERED CHECKS (stated before any 5.0 data)

All on the first scored 5.0 build, per class, reported beside coverage/rank; outcomes change the *next* generation only.
- **A.** Among near-miss-only overlaps (B below), compare `at_junction` vs non-junction hit rates; if junction-only beats non-junction and the rolling control, R1 becomes the promotion scope. Kind unchanged either way.
- **B.** Held-out events overlapped by a near-miss window and by no contact window of the class, vs the frozen 20-per-event rolling-span controls applied to near-miss windows; promotion to a scored lower-standing candidate requires near-miss-only hits above control expectation **and** every class in band with them admitted.
- **C.** Bereavement P4 admitted-day share with/without K-B; if K-B lifts it above 2.61 % where it was inside without, K-B → SUPPORT for bereavement (the DVI 40 % mechanism).
- **D.** P1 share and T-cover with/without kārakatva licences; revert to testimony where kārakatva-only windows push a class out of band it was inside, or where their held-out overlap rate does not exceed control.
- **E.** Slow-only vs all-agent-union variant: fast agents return as co-admitters for a class only if the union variant adds ≥ 2 held-out hits for that class **and** keeps it in band **and** does not void its rank eligibility. If slow-only still exceeds a class's band, that is a path-standing/houses question for the owner — never a licence to re-admit fast agents or re-pick houses.

## WHAT I DID NOT VERIFY

Verse bodies behind the Phaladīpikā TOC loci (XV.15–24, XXIII.13) and BPHS PG880's chapter context; Sanskrit of anything; whether `find_verses_about` with `text_ids` filters searches the full HIGH corpus (three filtered searches returned zero rows, so "not located" is bounded by that tool); the YJ chapter→planet map (memo's claim; YJ-filtered searches returned nothing); the day-share arithmetic is sign-bin geometry, not measured days; `admission.py`'s 5° vs `ORB_TABLE` 1° is read from source, not from a built ledger; no test, build or DB touched; no files modified.