---
artifact: MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE
version: "1.0"
status: SOURCE_PACKET_ACCEPTED_PROVENANCE_LOCAL
observed_at: 2026-09-15T06:54:00+05:30
strategy_decision: DP-SD-017
w0_accepted_source_tip: 00a161195
initial_candidate_tip: b0c5652ba290a9fc1283bc2adc25036549cec036
implementation_tip: 47131772b355ae2c67b1f6fb2b90e9fa007e2202
reviewed_tip: 47131772b355ae2c67b1f6fb2b90e9fa007e2202
packet: L3-W2-FIRST-FRONTIER-SOURCE-01
physical_w1: HELD
ri01: HELD_ON_RATIFICATION_AND_ROLE_CUTOVER
---

# L3 W2 first-frontier source packet

## 1. Authority and boundary

W0 explicitly permits source/service preparation for the first frontier while
physical W1 is held. This packet touches only the eight first-row-frontier
writers and the four independent service/pure identities. It does not apply a
migration, build a chart, select or accept a physical generation, change the
retired sweep, deploy code, exercise a consumer, or enter L4/L5.

The physical frontier remains blocked on an accepted/deployed RI-01 precursor
and a compatible L0-L2 generation vector. Source qualification here cannot
unlock a descendant or stand in for candidate-data acceptance.

## 2. Source corrections

The previous implementations could delete a chart partition before learning
that the replacement candidate was empty or that upstream coverage was only
partial. Initial candidate `b0c5652ba` plus corrections `a1767bb91` and
`47131772b` change the following source-local behavior:

- `ka_gochara_resonance`, `ka_kota_chakra`, `ka_moorti_nirnaya`,
  `ka_vedha_gochara`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`, `ka_yojaka`
  and `ka_avadhi` prepare and validate their candidate before DELETE;
- Kota, Moorti and Vedha require one unique, ordered row for every body and
  every inclusive horizon day. Avadhi imports the canonical seven-system set,
  including `chara_karaka`, and requires both MD and AD coverage;
- Gochara Resonance requires a non-empty candidate for every one of its 27
  event-class partitions before chart-wide replacement;
- `ka_yojaka` and `ka_avadhi` now return directly from `dry_run` before any
  database cursor is opened, and both return their canonical asset identity on
  dry-run, preservation and success paths;
- `ka_dasha_kala` rejects empty/unknown system requests and invalid intervals,
  and a single system-read failure aborts the whole call rather than returning
  a partial result that still lists the failed system as queried;
- `ka_tulana` rejects duplicate identities, invalid date bounds, unknown
  confidence/domain values, negative rarity and non-finite scores; its fixed
  forensic composite remains `0.7950` versus `0.4234`, with the same winner and
  decisive factor.

`ka_graha_sancara` and `ka_muhurta_seva` require no runtime change in this
packet. Their public payload shapes are frozen alongside Dasha and Tulana by the
new DB-free contract suite.

## 3. Verification

| Gate | Result | Qualification |
|---|---|---|
| Red-first W2 contract | 13 failed, 1 passed before implementation | Demonstrated the partial-response and unqualified-input gaps plus the initially misordered Muhurat fixture assertion. |
| Initial exact-tip review | REQUEST CHANGES at `b0c5652ba` | Found two HIGH and four MED correctness/preservation/test defects; the initial candidate was not accepted. |
| Corrected affected suite | 482 passed, 5 skipped | Covers all twelve packet identities plus behavioral replacement safety; skips are explicitly environment-gated. |
| Corrected behavioral contract | 57 passed | Recording fake connections prove no mutation on incomplete/interrupted candidates and DELETE-after-complete behavior. |
| Complete `tests/l3` | 1,521 passed, 41 skipped, 2 expected failures | Broad source regression only; warnings are pre-existing integration-mark/deprecation warnings. |
| Python compile | PASS | All changed modules and the new contract test compile. |
| `git diff --check` | PASS | No whitespace error. |
| First corrected-tip re-challenge | REQUEST CHANGES at `a1767bb91` | Found two MED anonymous-WriterResult identity defects; no prior finding reopened. |
| Final exact-tip review | PASS at `47131772b355ae2c67b1f6fb2b90e9fa007e2202` | Zero CRITICAL/HIGH/MED/LOW findings; reviewer focused gate 204 passed, 5 skipped. |
| L3 writer inventory reconciliation | PASS, source-local | Exactly ten reviewed W2 `ka_*` digests changed; unrelated `ka_sangam` and all non-L3 values remain preserved. |
| L3 layer-pin derivation | PASS, source-local | L3 aggregate `a32b7cc7b4fc82cce56ffa2d84331633bc75dd5c39fd829a303a269f3ebb9667`, convergence tip `47131772b…`; receipt count/non-writer set unchanged. |
| Whole pin check | EXPECTED HOLD | Fails only protected L0/L1/L2/L4 aggregates; live-source inventory remains held for 23 L2 identities plus unrelated `ka_sangam`. |

## 4. Holds and next action

The source packet is accepted at exact reviewed tip
`47131772b355ae2c67b1f6fb2b90e9fa007e2202`, with its ten source-owned writer
digests and L3 aggregate reconciled locally. This is source acceptance only.
RI-01, shared release and physical W1 remain held on the separately recorded
protected-pin and administrator-owned database role/credential/ownership
authorities.

No PR, push, shared migration apply, build, materialization, deployment,
integration, consumer-value proof or empirical evaluation is claimed.
