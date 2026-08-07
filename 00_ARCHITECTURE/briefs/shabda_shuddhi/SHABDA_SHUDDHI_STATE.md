---
artifact: SHABDA_SHUDDHI_STATE
canonical_id: SHABDA_SHUDDHI_STATE
version: rolling
status: LIVE
campaign: SHABDA-SHUDDHI (purification of the word)
created: 2026-08-07
single_writer: CONDUCTOR (claude-opus-4-6)
integration_branch: shabda-shuddhi/integration
cut_from: main @ 10bf3bdd6 (2026-08-07)
predecessor_campaign: SAD-DARSHANA (PARKED-FINAL, RUN-TERMINAL at HB #113)
---

# SHABDA-SHUDDHI Campaign State Ledger

Single-writer discipline: only the CONDUCTOR appends entries. All entries
attributed and timestamped.

---

## RUN-OPEN — 2026-08-07T10:25:00Z (CONDUCTOR, run-1)

### Pre-flight verified

- main == production: Deploy SUCCESS at 10bf3bdd6, all 5 CI checks green
- corpus counts (carry-forward from W2 CLOSE, R1 untouchable):
  606/606 sweep substeps; kala_gochara_windows 482012f1=16,297 / 1c826d5a=19,323
- zero in-flight PRs: only PRESERVE #898/#899 + stale docs #446
- worktrees: 9 SAD-DARSHANA worktrees all clean (no salvage needed)
- integration branch: shabda-shuddhi/integration cut from main @ 10bf3bdd6

### Native rulings (ratified 2026-08-07, final)

**R6. PROMISE IS A MODIFIER, NEVER A GATE.** Every class with an N_e prior
computes a hazard field; promise scales via the Adrsta floor (C-2), never
excludes. Three serving tiers: promised/conditional = full serve;
denied/no_evidence = COMPUTED + LABELED falsification-tier (always scored,
served only with explicit tier label per N.6); no-prior = honest
ClassSkipped. All five categorical gates convert to this semantics.

**R7. ONE CANONICAL 13-DOMAIN VOCABULARY.** Promote ph_nimitta's constant +
synonym map to a shared module (Python + mirrored TS constant, CI-diffed
per the existing rail); retire all nine variants. bo_laksana's three maps
rebuilt on the full vocabulary per CLASSICAL significations, each mapping
row carrying a classical citation (B.3 derivation-ledger discipline;
PARIKSHAKA verifies citations resolve against the corpus): 5th house +=
progeny; 4th += residence, education; 9th += travel; 12th += travel/foreign;
2nd += family; D7 varga -> progeny; D4 -> residence; Jupiter putrakaraka
routes. Valence: mixed and neutral are WEIGHTED evidence, never discarded.

**R8. NO VERDICT FROM ZERO EVIDENCE, platform-wide.** bodha_pratijna gains
status 'no_evidence' (CHECK constraint migration; kala_lattice_query
template); every P2-class site in the dossier fixed to the same standard
(empty != clean, empty != light, empty != denied).

**R9. REBUILD after engine fixes:** full bodha->kala->phala->mimamsa chain for
the three live charts (482012f1, 1c826d5a, cb73cd3d); the six contaminated
tables regenerate; Maha-Brief verdict content re-derives.

### Declared defaults (unchanged)

- LEL entries native-only; Lane L6 resolver classifies deterministically
  with audit trail; AMBIGUOUS mappings PARK for native review.
- No new N_e priors.
- FROZEN-contract changes park.
- Sweep corpus untouchable (R1 permanent).
- FIRST-SCORE-BECOMES-BASELINE is the arc's one irreversible artifact.

### Execution DAG position

STAGE 0 (PRE-FLIGHT): COMPLETE
STAGE V0 (VOCABULARY MODULE): COMPLETE (PARIKSHAKA ACCEPT 8/8, 18/18 tests)
STAGE 1 (FAN-OUT L1-L8): DISPATCHING
STAGE R (REBUILD): PENDING (blocked on L1-L5 merged)
STAGE S (FIRST SKILL SCORE): PENDING (blocked on R)
CLOSE: PENDING

---

## V0 COMPLETE — 2026-08-07T10:35:00Z (CONDUCTOR)

Deliverables:
- brahmagyan/domain_vocabulary.py: CANONICAL_DOMAINS (13), DOMAIN_SYNONYMS (19),
  canonical_domain(), is_canonical(), assert_canonical()
- platform/src/lib/domain_vocabulary.ts: TS mirror (exact parity)
- tests/test_domain_vocabulary.py: 18 tests (vocabulary, parity, migration 386)

PARIKSHAKA verdict: ACCEPT (8/8 items PASS)
Commit: c3ef13e3a on shabda-shuddhi/integration

---

## STAGE 1 DISPATCH — 2026-08-07T10:36:00Z (CONDUCTOR)

Round 1 (independent of each other, all depend on V0 only):
- L1 bo_laksana remap: 3 maps -> 13 domains, citation-backed
- L2 bo_pratijna v2: class-level routing, 'no_evidence' status + migration
- L4 numeric fixes: _promise_lift inversion, ka_yojaka, taranga_service
- L5 dead junctions: ka_bhavishya_lekha, prashna, ph_phaladesa, registry_bridge, etc.
- L6 LEL->event_class resolver
- L8 detectors: junction hit-rate, CI vocabulary-census, empty-evidence lint

Round 2 (blocked on L2 'no_evidence' migration):
- L3 gates->R6: five categorical gates -> modifier semantics
- L7 serving guards: query_pratijna, mi_darshana, synth brief

---

## L1 COMPLETE — 2026-08-07T10:43:00Z (CONDUCTOR)

bo_laksana.py remapped to full 13-domain vocabulary:
- _BHAVA_DOMAINS: expanded from 6 to 12 unique domains + 'general' fallback;
  classical citations per B.3 (BPHS ch.11, ch.6, ch.30, ch.32, ch.34-39)
- _DOMAIN_MAP: 48 entries selectively expanded (yoga/dosha/karaka/arudha/
  sade_sati/lord-in-house/bhava categories gain progeny/education/family/
  residence/travel/transition)
- _CATEGORY_DEFAULT_DOMAINS: 10 subsystem defaults expanded
- CR-62 varga gate: extended with D7->progeny, D4->residence, D24->education,
  D12->travel (BPHS ch.6)
- Fallback: ["career","character"] -> ["general"]
- Imports CANONICAL_DOMAINS from brahmagyan.domain_vocabulary

Domain coverage: 12/13 in explicit maps, 'general' as fallback = all 13 reachable.
PARIKSHAKA: PENDING (to be dispatched when builders complete).
Commits: 2a59931ed (L1) + 8ce882909 (L8 domain_lookup) on integration.

## L8 PARTIAL — 2026-08-07T10:43:00Z (CONDUCTOR, consolidating builder output)

domain_lookup() junction hit-rate telemetry landed on integration.
7 tests added to test_domain_vocabulary.py (25/25 total PASS).
Remaining L8 items (CI census gate, empty-evidence lint): builder in progress.

## Builders in flight: L2, L4, L5, L8 (background agents)

---
