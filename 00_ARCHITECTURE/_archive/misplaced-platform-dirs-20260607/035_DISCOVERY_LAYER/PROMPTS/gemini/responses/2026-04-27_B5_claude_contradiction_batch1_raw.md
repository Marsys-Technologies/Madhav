---
prompt_id: claude.contradiction_scan
version: "1.0"
batch_id: batch1
produced_on: 2026-04-27
pass_type: CLAUDE_PROPOSER_PASS_1
session: Madhav_M2A_Exec_11
hypothesis_count: 10
self_audit_summary: "SELF-AUDIT: 10 hypotheses proposed. 2 likely to be rejected by Gemini (CH.006 resolvable by reading signals together; CH.010 timing windows non-overlapping). 8 genuine structural conflicts."
---

```yaml
contradiction_hypotheses:
  - hypothesis_id: "CH.001"
    contradiction_class: "signal_polarity_conflict"
    hypothesis_text: "SIG.MSR.107 asserts Saturn 7H exaltation delays committed partnership; SIG.MSR.122 asserts Saturn 7H exaltation produces strong, disciplined partnership — the same planetary position produces opposite relational outcomes."
    mechanism: "Both signals invoke Saturn's 7H exaltation as their structural anchor. SIG.MSR.107 reads the exaltation through the lens of Saturn's natural karakatva for delay and restriction, concluding that marriage is postponed. SIG.MSR.122 reads the same exaltation as conferring depth and permanence to committed relationships, concluding that Saturn's strength actually supports long-term partnership. These are mechanically opposed: delay vs. depth implies fundamentally different guidance about when and whether to commit."
    domains_implicated:
      - relationships
      - career
    signals_in_conflict:
      - "SIG.MSR.107"
      - "SIG.MSR.122"
    l1_references:
      - "FORENSIC_v8_0 §Saturn: Libra 7H, 22°27′04″ Vishakha — Exalted (AK)"
      - "FORENSIC_v8_0 §Mars: Libra 7H, 18°31′38″ Swati — Co-occupant of 7H"
    claude_severity_prior: HIGH
    resolution_options:
      - "Option A: Qualify both signals by dasha period — Saturn dasha activates strength (SIG.MSR.122); non-Saturn periods activate delay (SIG.MSR.107)."
      - "Option B: Retain both with explicit note that they represent different interpretive schools (Parashari delay vs. Jaimini strength-emphasis) and flag for native's consultation."
      - "Option C: Flag SIG.MSR.107 as L1-grounded and SIG.MSR.122 as L2 derivative needing explicit derivation chain."

  - hypothesis_id: "CH.002"
    contradiction_class: "karaka_ambiguity"
    hypothesis_text: "Saturn as simultaneous AK (soul-dharma) and AmK (vocational) produces structurally incompatible predictions: AK activation during Saturn dasha should push toward renunciation and inward spiritual turn, while AmK activation should push toward career expansion and external recognition."
    mechanism: "The dual-karaka confluence means that during Saturn's mahadasha/antardasha, both the AK engine (soul-purpose revision, potentially world-renunciation or deep introspection) and the AmK engine (career acceleration, status recognition, vocational authority) fire simultaneously from the same planet. Multiple MSR signals engage Saturn as career indicator (AmK function); others engage it as soul-dharma indicator (AK function). When a signal says 'Saturn dasha brings career recognition' it uses AmK logic; when another says 'Saturn dasha brings spiritual withdrawal' it uses AK logic — these cannot both be maximally true in the same time window without acknowledgment of the tension."
    domains_implicated:
      - career
      - spiritual
      - mind
    signals_in_conflict:
      - "SIG.MSR.012"
      - "SIG.MSR.363"
    l1_references:
      - "FORENSIC_v8_0 §Saturn: Libra 7H, 22°27′04″ Vishakha — AK + AmK (dual-karaka)"
      - "PHASE_B_PLAN §B.5 karaka_ambiguity scan"
    claude_severity_prior: HIGH
    resolution_options:
      - "Option A: Require all Saturn-dasha signals to declare which karaka function they invoke (AK or AmK) and add a corpus-wide annotation pass."
      - "Option B: Model as a sequencing within the period — early Saturn dasha activates AmK (career), late Saturn dasha activates AK (spiritual reorientation) — requires dasha sub-period precision."
      - "Option C: Accept both as co-active with different domains of expression (career-external vs. spiritual-internal), requiring explicit framing in any consultation output."

  - hypothesis_id: "CH.003"
    contradiction_class: "domain_cross_claim"
    hypothesis_text: "SIG.MSR.288 (Mars PK indicates biological children are delayed or limited) and SIG.MSR.303 (Mars Lagna lord's vitality confers strong first-child timing) make incompatible predictions about the native's progeny timing."
    mechanism: "SIG.MSR.288 grounds its claim in Mars's Avayogi status (fortune-reducer) overlaid on its PK role, concluding that Mars as the children-karaka is compromised and progeny are likely delayed or require special dasha activation. SIG.MSR.303 grounds its claim in Mars's Lagna-lord function (vitality + first-breath signification) which traditionally signals readiness for first-child expression. The conflict is not just interpretive — one predicts delay, the other predicts organic timing — and no signal explicitly reconciles the Avayogi suppression with the Lagna-lord momentum."
    domains_implicated:
      - children
      - health
    signals_in_conflict:
      - "SIG.MSR.288"
      - "SIG.MSR.303"
    l1_references:
      - "FORENSIC_v8_0 §Mars: Libra 7H, 18°31′38″ Swati — PK (Putrakaraka) + Avayogi + Lagna Lord"
    claude_severity_prior: HIGH
    resolution_options:
      - "Option A: Introduce an explicit hierarchy: Avayogi status suppresses the PK function during non-Mars periods, while Mars dasha/antardasha reactivates it — reconciling both signals as period-specific."
      - "Option B: Flag SIG.MSR.303 for re-derivation — it may conflate Lagna-lord vitality (health domain) with progeny timing (children domain), a domain cross-bleed violation."

  - hypothesis_id: "CH.004"
    contradiction_class: "p6_uvc_conflict"
    hypothesis_text: "SIG.MSR.055 claims Rahu 2H drives wealth accumulation through unconventional channels; CDLM records a cross-domain link between 2H Rahu and 8H Ketu that modulates 2H gains through sudden losses — these two representations are in structural tension."
    mechanism: "SIG.MSR.055 uses Rahu's 2H placement as a unidirectional wealth-accumulation signal (desire → acquisition). The CDLM's 2H-8H Rahu-Ketu axis captures a bidirectional modulation: Rahu amplifies 2H accumulation while Ketu simultaneously depletes through 8H sudden events. The signal captures only the amplification vector without the depletion counter-vector that the CDLM cell records. A corpus that contains SIG.MSR.055 (unidirectional) and the CDLM entry (bidirectional) is internally inconsistent — reading SIG.MSR.055 alone would give the native an incomplete and potentially misleading picture of their wealth dynamics."
    domains_implicated:
      - wealth
    signals_in_conflict:
      - "SIG.MSR.055"
      - "SIG.MSR.082"
    l1_references:
      - "FORENSIC_v8_0 §Rahu: Taurus 2H"
      - "FORENSIC_v8_0 §Ketu: Scorpio 8H"
      - "CDLM v1.2 — 2H/8H nodal axis cell"
    claude_severity_prior: MED
    resolution_options:
      - "Option A: Add a qualifying clause to SIG.MSR.055 referencing the Ketu 8H counter-vector explicitly."
      - "Option B: Create a cross-reference signal that explicitly models the net wealth dynamic across both nodes."

  - hypothesis_id: "CH.005"
    contradiction_class: "timing_conflict"
    hypothesis_text: "SIG.MSR.241 predicts peak intellectual output during Mercury dasha; SIG.MSR.267 predicts peak intellectual output during Moon dasha (Yogi activation). These predictions cannot both be 'peak' — one must be the actual career-intellectual apex."
    mechanism: "Both signals invoke 'peak' framing for the same life domain (intellectual/communication output) but anchor to different planetary periods: Mercury (Vargottama, 10H) for SIG.MSR.241 and Moon (Yogi, 11H) for SIG.MSR.267. If both are correct, the native experiences two separate peaks — but neither signal qualifies the claim relative to the other. This is a timing conflict that would produce confused guidance: 'when is the best time to launch your intellectual work?' has two incompatible answers from the same corpus."
    domains_implicated:
      - career
      - mind
    signals_in_conflict:
      - "SIG.MSR.241"
      - "SIG.MSR.267"
    l1_references:
      - "FORENSIC_v8_0 §Mercury: Capricorn 10H, Vargottama"
      - "FORENSIC_v8_0 §Moon: Aquarius 11H, Yogi planet"
    claude_severity_prior: MED
    resolution_options:
      - "Option A: Qualify SIG.MSR.241 as 'peak self-expression via analytical output' and SIG.MSR.267 as 'peak social-network-amplified reach' — distinguishing quality vs. audience."
      - "Option B: Establish a hierarchy: Mercury dasha (Vargottama + 10H) is primary peak; Moon antardasha within Mercury is secondary amplification."

  - hypothesis_id: "CH.006"
    contradiction_class: "signal_polarity_conflict"
    hypothesis_text: "SIG.MSR.158 (Ketu 8H confers occult/spiritual mastery through isolation) and SIG.MSR.172 (Ketu 8H creates anxiety about endings and sudden loss) appear to conflict but may resolve when domains are properly separated."
    mechanism: "SIG.MSR.158 reads Ketu 8H through the lens of past-life mastery and moksha-oriented detachment, yielding a positive spiritual outcome. SIG.MSR.172 reads the same placement through the lens of 8H anxiety, hidden fears, and sudden-loss trauma. These are not structurally opposed — they apply to different domain registers (spiritual vs. psychological/health) — but the corpus does not make this domain separation explicit, potentially creating misleading cross-domain reading in consultation."
    domains_implicated:
      - spiritual
      - health
      - mind
    signals_in_conflict:
      - "SIG.MSR.158"
      - "SIG.MSR.172"
    l1_references:
      - "FORENSIC_v8_0 §Ketu: Scorpio 8H"
    claude_severity_prior: LOW
    resolution_options:
      - "Option A: Add explicit domain annotations to both signals to prevent cross-reading."
      - "Option B: Accept as co-active in different registers — spiritual mastery and psychological vulnerability are non-exclusive."

  - hypothesis_id: "CH.007"
    contradiction_class: "p1_layer_bleed"
    hypothesis_text: "SIG.MSR.322 states 'Sun in 10H produces public leadership role' — this is an L2 interpretation stated without a derivation chain to the L1 Sun position (Capricorn 10H, Shravana, 21°57′35″). The claim may be sound but is stated as L1 fact."
    mechanism: "The signal text for SIG.MSR.322 uses declarative assertion language ('produces') without explicitly citing the L1 position and the classical rule that translates Sun-in-10H into 'leadership role.' Per B.1 (Facts/Interpretation separation), an interpretation must cite the L1 fact + the classical derivation rule that produces it. Without the explicit chain, the signal is an L2 claim masquerading as an L1 datum, which is a p1_layer_bleed violation that corrupts the derivation ledger's auditability."
    domains_implicated:
      - career
      - parents
    signals_in_conflict:
      - "SIG.MSR.322"
      - "SIG.MSR.338"
    l1_references:
      - "FORENSIC_v8_0 §Sun: Capricorn 10H, 21°57′35″ Shravana"
      - "PROJECT_ARCHITECTURE §B.1 — Facts/Interpretation separation"
    claude_severity_prior: MED
    resolution_options:
      - "Option A: Add explicit derivation chain to SIG.MSR.322: L1 (Sun 10H Capricorn) + classical rule (BPHS Chapter X) → L2 claim (leadership role)."
      - "Option B: Mark SIG.MSR.322 as [DERIVATION_CHAIN_PENDING] and queue for next session cleanup."

  - hypothesis_id: "CH.008"
    contradiction_class: "domain_cross_claim"
    hypothesis_text: "SIG.MSR.414 (Moon Yogi 11H brings fortune through group networks) and SIG.MSR.436 (Moon Yogi 11H brings fortune through solitary philosophical work) are incompatible: the same planetary placement cannot simultaneously signal group-based and solitary-work fortune vectors."
    mechanism: "Both signals ground their claim in Moon's Yogi designation and 11H placement, but diverge on the mode of fortune delivery. SIG.MSR.414 reads Aquarius 11H as group-network fortune (Aquarius = universal, communal). SIG.MSR.436 reads Purva Bhadrapada nakshatra (Jupiter-ruled, fiery, associated with ascetic disciplines) as solitary philosophical fortune. These two vectors are not just different emphases — they prescribe materially different behavioral strategies to the native (network vs. withdrawal). A corpus that contains both without hierarchy creates contradictory guidance."
    domains_implicated:
      - wealth
      - career
      - mind
    signals_in_conflict:
      - "SIG.MSR.414"
      - "SIG.MSR.436"
    l1_references:
      - "FORENSIC_v8_0 §Moon: Aquarius 11H, 27°02′48″ Purva Bhadrapada — Yogi"
    claude_severity_prior: MED
    resolution_options:
      - "Option A: Establish that Aquarius sign governs the mode (group network) while Purva Bhadrapada nakshatra governs the style of contribution (philosophical depth) — both true but at different levels of description."
      - "Option B: Qualify SIG.MSR.436 as applying during Ketu antardasha (co-ruler of Purva Bhadrapada nakshatra chain) specifically."

  - hypothesis_id: "CH.009"
    contradiction_class: "classical_basis_conflict"
    hypothesis_text: "SIG.MSR.462 cites BPHS's Parashari rule for Jupiter-Venus conjunction producing wealth yoga; SIG.MSR.469 cites the Jaimini KarakaAmsha rule which does not recognize Jupiter-Venus conjunction as a wealth yoga in D9 — these classical bases are incompatible for this chart's specific combination."
    mechanism: "The Jupiter-Venus conjunction in Sagittarius 9H is assessed differently under Parashari and Jaimini frameworks. Under Parashari (BPHS): Jupiter + Venus in a kendra or trikona from Lagna or Moon produces a Dhana yoga, and 9H qualifies under both Lagna and Moon counts. Under Jaimini KarakaAmsha: the same conjunction must be evaluated in the D9 chart's AK house, not the D1 9H, and Jupiter-Venus conjunction in D9 carries different significations. SIG.MSR.462 uses Parashari framing; SIG.MSR.469 uses Jaimini framing. The corpus does not declare which framework governs this specific claim, producing a classical_basis_conflict that affects how any consultation interprets the 9H conjunction's wealth implications."
    domains_implicated:
      - wealth
      - spiritual
    signals_in_conflict:
      - "SIG.MSR.462"
      - "SIG.MSR.469"
    l1_references:
      - "FORENSIC_v8_0 §Jupiter: Sagittarius 9H, 09°48′28″ Moola"
      - "FORENSIC_v8_0 §Venus: Sagittarius 9H, 19°10′12″ Purva Ashadha"
    claude_severity_prior: MED
    resolution_options:
      - "Option A: Tag each signal with its governing framework (parashari|jaimini) and require all consultation outputs to declare which framework governs their reading."
      - "Option B: Accept both frameworks as valid and require the native to select the preferred lineage for actionable guidance."

  - hypothesis_id: "CH.010"
    contradiction_class: "timing_conflict"
    hypothesis_text: "SIG.MSR.395 and SIG.MSR.402 both predict career authority consolidation during Saturn antardasha within Jupiter mahadasha — but their predicted mechanisms are mutually exclusive within a single antardasha window."
    mechanism: "SIG.MSR.395 predicts career authority consolidation through external institutional recognition (promotion, title, recognition from authority figures) during Saturn antardasha in Jupiter mahadasha. SIG.MSR.402 predicts the same period as one of internal restructuring and withdrawal from external validation (Saturn as AK pulling inward). These mechanisms are temporally incompatible within a single antardasha — a period cannot simultaneously be one of peak external recognition and peak internal withdrawal. However, the antardasha sub-division (Pratyantardasha) could resolve this by sequencing the mechanisms, which neither signal acknowledges."
    domains_implicated:
      - career
      - spiritual
    signals_in_conflict:
      - "SIG.MSR.395"
      - "SIG.MSR.402"
    l1_references:
      - "FORENSIC_v8_0 §Saturn: Libra 7H — AK + AmK"
      - "FORENSIC_v8_0 §Jupiter: Sagittarius 9H — 9H placement"
    claude_severity_prior: LOW
    resolution_options:
      - "Option A: Resolve by Pratyantardasha sub-division — external recognition in early Saturn antardasha; AK-driven inward turn in late Saturn antardasha."
      - "Option B: Accept as co-active at different levels of the native's experience (external career vs. internal soul-arc) — not a conflict but a dual-register activation."
```
